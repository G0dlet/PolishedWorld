"""
Knowing people: `recog` and `forget`. Names, Task NM-T5
(docs/PolishedWorld_Combat_Decomposition.md, NM4; Names note UP5, UP7, UP8).

A stranger is known by how they look. `recog <description> as <name>` puts a
name of the player's own choosing on a person in the room -- the knower's
memory, which can be wrong or misled (a naming system, Names note §2.3) --
and `forget <name>` takes it off again, from anywhere.

WHY NOT THE CONTRIB'S CmdRecog
------------------------------
The rpsystem contrib's `recog` (rpsystem.py:1123) takes its candidates from
the room's whole contents (`:1191`), so a creature, an item and the caller
can all be "recognised"; it catches only `RecogError` (`:1230`) while the
handler also raises `SdescError` (`:810`, `:825`); and its `forget` resolves
the name against the room (`:1192`), so a person who has left cannot be
forgotten (UP7). The handler underneath -- `caller.recog`, a `RecogHandler`
(`:754`) -- is the contrib's, used as it is (NM4).

WHAT THE LIST SHOWS (lock 1 B, Adam 2026-11-15)
-----------------------------------------------
A label, and how the person looks now only while they stand in the same
room. The short description will be live (OQ-NM9): sores, wet clothes, the
cloak worn today. Read from anywhere, the list would be a spyglass.

A LABEL HELD FOR TWO (lock 2 B)
-------------------------------
Labels are free and identical descriptions are allowed (UP4), so a player
can know two people as *Tess*. `RecogHandler.all()` returns `{label: person}`
and keeps only one of them (run, 2026-11-15), so this module reads
`recog.obj2recog` instead. The list numbers a shared label in the game's
`N-name` form, in a fixed order (label, then the person's id), and `forget`
counts `N-` in the same order.

A STATUE (lock 3 A)
-------------------
A statue is the person, logged out. A recog belongs to the person, not to
the text, so a statue can be recognised like anyone else.

INTRODUCE (NM-T6; NM5, UP6, OQ-NM3 lock A)
------------------------------------------
`introduce` is the truthful side (Names note §2.3): it gives the speaker's
key, and cannot lie. Every awake character in the room reads one line naming
the speaker as that reader knows them, and only then is the recog written,
so a stranger reads the description and the name together. A hearer who has
already chosen a name for the speaker keeps it (NM5): what a player has
chosen to call someone is theirs (UG3). `introduce to <description>` gives
the name to one person; the room reads that an introduction was made, with
both people as each reader knows them, and without the name.

A statue hears nothing: its player is not there. The reflexive is
`$pron(yourself)`, read from the speaker's `gender` (NM-T15b): *himself*,
*herself*, or *themselves* for a character without the facts.

WHO (NM-T14; K1, UP14, UQ1)
---------------------------
Evennia's `who` gave every player a table of every connected account, and
an account's name is its character's key (Evennia's
`AUTO_CREATE_CHARACTER_WITH_ACCOUNT`). `CmdWho` gives an account with Builder or above Evennia's command
unchanged (lock 2 A), and anyone else one sentence with the count (lock 1
A): *seven travellers are abroad in the world*, the reader counted, the
number in words to twenty. A list of the people you know who are online is
left out (UQ1): it would tell you where your friends are not.

MULTIPLAYER
-----------
A recog is written only on its owner, by its owner's command (Names UG6):
two players recognising the same person write two different Attributes, and
nothing ticks. The push to the webclient is NM-T17's.
"""

import re

import evennia
from django.conf import settings
from evennia import Command
from evennia.commands.default.account import CmdWho as _EvenniaCmdWho
from evennia.contrib.rpg.rpsystem import rpsystem as _rp
from evennia.contrib.rpg.rpsystem.rpsystem import CmdEmote as _ContribCmdEmote
from evennia.contrib.rpg.rpsystem.rpsystem import CmdPose as _ContribCmdPose
from evennia.contrib.rpg.rpsystem.rpsystem import CmdSay as _ContribCmdSay
from evennia.contrib.rpg.rpsystem.rpsystem import EmoteError, RecogError, SdescError
from evennia.utils import ansi, logger
from evennia.utils.utils import inherits_from

_CHARACTER = "typeclasses.characters.Character"
_MULTIMATCH_REGEX = re.compile(settings.SEARCH_MULTIMATCH_REGEX, re.I + re.U)

# The handler's own limit (RecogHandler.add, max_length=60).
MAX_LABEL = 60

_COUNT_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def held_names(knower):
    """
    Everyone `knower` holds a name for, as `(label, person)` pairs, in the
    order the list shows them and `forget` counts them: by label without
    regard to case, then by the person's id. A person who no longer exists
    is left out.
    """
    pairs = [
        (label, person)
        for person, label in knower.recog.obj2recog.items()
        if person and label
    ]
    return sorted(pairs, key=lambda pair: (pair[0].lower(), pair[1].id))


def _numbered(held):
    """
    The held pairs as the list writes them: a label shared (without regard
    to case) by more than one person gets its `N-` number, counted within
    that label; a label held once is written as it is.
    """
    counts = {}
    for label, _person in held:
        counts[label.lower()] = counts.get(label.lower(), 0) + 1
    seen = {}
    written = []
    for label, person in held:
        if counts[label.lower()] > 1:
            seen[label.lower()] = seen.get(label.lower(), 0) + 1
            written.append((f"{seen[label.lower()]}-{label}", person))
        else:
            written.append((label, person))
    return written


class CmdRecog(Command):
    """
    Put a name to a face, or list the names you hold.

    Usage:
      recog
      recog <description> as <name>

    Examples:
      recog lanky as Tess
      recog 2-lanky as Maren

    A stranger is known by how they look. Once you give someone a name, you
    see that name wherever you meet them, and you can use it to point at
    them. The name is yours alone: nobody else sees it, and it may be wrong.

    With no arguments, lists everyone you know by name; those in the room
    with you are shown with how they look now.

    See also: forget
    """

    key = "recog"
    locks = "cmd:all()"
    help_category = "General"

    def parse(self):
        self.target, self.label = "", ""
        args = self.args.strip()
        if " as " in args:
            target, label = args.split(" as ", 1)
            self.target, self.label = target.strip(), label.strip()

    def func(self):
        caller = self.caller
        if not self.args.strip():
            self.list_names()
            return
        if not (self.target and self.label):
            caller.msg("Usage: recog <description> as <name>")
            return
        if self.target.lower() in ("me", "self"):
            caller.msg("You know who you are.")
            return
        location = caller.location
        if not location:
            caller.msg("There is no one here to know.")
            return

        candidates = [
            obj
            for obj in location.contents
            if obj != caller and inherits_from(obj, _CHARACTER)
        ]
        person = caller.search(self.target, candidates=candidates)
        if not person:
            return  # the search has told the caller
        if person == caller:
            caller.msg("You know who you are.")
            return
        if not person.access(caller, "enable_recog", default=True):
            caller.msg("You cannot make out who they are.")
            return

        # A name carries no colour (NM11): the contrib stores the text as
        # typed, colour codes and all (rpsystem.py:836).
        label = ansi.strip_ansi(self.label).rstrip(".?!").strip()
        if not any(char.isalnum() for char in label):
            # The handler strips `/word` emote markers but keeps a bare `/`
            # or `-` as a label (run, 2026-11-15).
            caller.msg("That is not a name you can keep.")
            return
        if len(label) > MAX_LABEL:
            caller.msg("That name is too long to keep in mind.")
            return
        known_as = caller.get_sdesc(person, process=True)
        try:
            label = caller.recog.add(person, label, max_length=MAX_LABEL)
        except RecogError:
            caller.msg("That name is too long to keep in mind.")
            return
        except SdescError:
            # An empty name once the emote markers are stripped, or the
            # person's own lock: either way nothing was written.
            caller.msg("That is not a name you can keep.")
            return
        except Exception:
            logger.log_trace(f"Names: recog failed for {caller.dbref} -> {person.dbref}")
            caller.msg("The name will not stick just now.")
            return
        caller.msg(f"You will remember {known_as} as {label}.")

    def list_names(self):
        caller = self.caller
        held = _numbered(held_names(caller))
        if not held:
            caller.msg("You know no one by name yet.")
            return
        here = caller.location
        lines = []
        for written, person in held:
            if here and person.location == here and hasattr(person, "sdesc"):
                lines.append(f" {written} ({person.sdesc.get()})")
            else:
                lines.append(f" {written}")
        caller.msg("You know these people by name:\n" + "\n".join(lines))


def _awake_characters(location, caller):
    """The characters in `location` other than `caller` with a player in them."""
    return [
        obj
        for obj in location.contents
        if obj != caller and inherits_from(obj, _CHARACTER) and not obj.is_statue
    ]


def _remember(speaker, hearers):
    """
    Give each hearer the speaker's key as a recog, unless they already hold a
    name for the speaker (NM5). One hearer failing is logged and does not
    stop the others.
    """
    for hearer in hearers:
        try:
            if hearer.recog.get(speaker) is None:
                hearer.recog.add(speaker, speaker.key)
        except Exception:
            logger.log_trace(
                f"Names: introduce could not write {hearer.dbref}'s recog of {speaker.dbref}"
            )


class CmdIntroduce(Command):
    """
    Tell people your name.

    Usage:
      introduce
      introduce to <description>

    Examples:
      introduce
      introduce to lanky

    Gives your true name to everyone awake in the room, or to one person.
    Those who had no name for you will know you by it; anyone who has
    already chosen a name for you keeps their own. When you introduce
    yourself to one person, the others see it happen but do not hear the
    name.

    See also: recog, forget
    """

    key = "introduce"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        location = caller.location
        if args and not args.lower().startswith("to "):
            caller.msg("Usage: introduce, or introduce to <description>")
            return
        if not location:
            caller.msg("There is no one here to hear you.")
            return
        mapping = {"truename": caller.key}

        if not args:
            hearers = _awake_characters(location, caller)
            if not hearers:
                caller.msg("There is no one here to hear you.")
                return

            def send():
                caller.msg(f"You introduce yourself as {caller.key}.")
                location.msg_contents(
                    "$You() introduces $pron(yourself) as {truename}.",
                    exclude=[caller] + [obj for obj in location.contents if obj not in hearers],
                    from_obj=caller,
                    mapping=mapping,
                )

        else:
            wanted = args[3:].strip()
            if wanted.lower() in ("me", "self"):
                caller.msg("You know who you are.")
                return
            candidates = [
                obj
                for obj in location.contents
                if obj != caller and inherits_from(obj, _CHARACTER)
            ]
            target = caller.search(wanted, candidates=candidates)
            if not target:
                return  # the search has told the caller
            if target.is_statue:
                caller.msg("They cannot hear you now.")
                return
            hearers = [target]
            bystanders = [obj for obj in _awake_characters(location, caller) if obj != target]
            shown = caller.get_sdesc(target, process=True)

            def send():
                caller.msg(f"You introduce yourself to {shown} as {caller.key}.")
                location.msg_contents(
                    "$You() introduces $pron(yourself) to you as {truename}.",
                    exclude=[obj for obj in location.contents if obj != target],
                    from_obj=caller,
                    mapping=mapping,
                )
                location.msg_contents(
                    "$You() introduces $pron(yourself) to {target}.",
                    exclude=[obj for obj in location.contents if obj not in bystanders],
                    from_obj=caller,
                    mapping={"target": target},
                )

        # The lines first, then the recogs: each reader reads the speaker as
        # they knew them before the command (NM-T6).
        send()
        _remember(caller, hearers)


class CmdForget(Command):
    """
    Let go of a name you have given someone.

    Usage:
      forget <name>
      forget <N>-<name>

    Examples:
      forget Tess
      forget 2-Tess

    Works wherever you are. If you know more than one person by the same
    name, `recog` lists them numbered; use the number to say which.

    See also: recog
    """

    key = "forget"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        name = self.args.strip()
        if not name:
            caller.msg("Usage: forget <name>")
            return

        held = held_names(caller)
        same = [pair for pair in held if pair[0].lower() == name.lower()]
        number = None
        if not same:
            match = _MULTIMATCH_REGEX.match(name)
            if match:
                number = int(match.group("number"))
                bare = match.group("name").strip().lower()
                same = [pair for pair in held if pair[0].lower() == bare]

        if number is not None:
            same = [same[number - 1]] if 1 <= number <= len(same) else []
        if not same:
            caller.msg(f"You know no one as {name}.")
            return
        if len(same) > 1:
            label = same[0][0]
            which = ", ".join(f"{num}-{label}" for num in range(1, len(same) + 1))
            count = _COUNT_WORDS.get(len(same), "several")
            caller.msg(f"You know {count} people as {label}: {which}.")
            return

        label, person = same[0]
        try:
            caller.recog.remove(person)
        except Exception:
            logger.log_trace(f"Names: forget failed for {caller.dbref} -> {person.dbref}")
            caller.msg("The name will not leave you just now.")
            return
        caller.msg(f"You let the name {label} go.")


# --------------------------------------------------------------------------
# Emotes: the contrib's parser, its leftover number removed (NM-T7, lock 1 C)
# --------------------------------------------------------------------------
#
# The contrib's emote parser leaves the number of a numbered reference in the
# text: `nods to /2-tall.` reaches the room as *nods to /2a tall man.* When a
# reference carries a number, its `head` is cut two characters after the `/`
# instead of at it (rpsystem.py:426-431), so `/2` stays in front of the
# `{#id}` marker that replaces the name. Every `/N-word` does it, `/1-` too,
# and a pose stores it. Run 2026-11-15; the same lines are on Evennia's
# `main` at 98b9df2 (2026-10-24), and the contrib's tests never try a number.
#
# The parser itself is taken as it is (OQ-NM8): a person the emoter knows by
# a recog and sees by a description is two rows, `N-` is counted in that
# list, and a number past the end names the last. Only the leftover text is
# removed, right after the parser and before the markers are formatted, so
# `send_emote` below is the contrib's (rpsystem.py:558-651) with that one
# call changed. The contrib's `emote`, `say` and `pose` call its module
# function directly, so each is subclassed to call these.

# The marker the parser writes: `{#<id>}` with an optional case flag
# (_get_case_ref, rpsystem.py:253: t, ^, v, ~).
_RE_LEFTOVER_NUMBER = re.compile(r"/[0-9]+(?=\{#[0-9]+[t^v~]?\})")


def parse_emote(sender, candidates, string, **kwargs):
    """
    The contrib's parse_sdescs_and_recogs (not in search mode), with the
    leftover `/N` of a numbered reference removed. Raises EmoteError as the
    contrib does.
    """
    emote, mapping = _rp.parse_sdescs_and_recogs(sender, candidates, string, **kwargs)
    return _RE_LEFTOVER_NUMBER.sub("", emote), mapping


def send_emote(sender, receivers, emote, msg_type="pose", anonymous_add="first", **kwargs):
    """
    The contrib's send_emote (rpsystem.py:558-651), calling parse_emote.

    Each receiver reads every person as that receiver knows them (recog, else
    short description); the sender is added at the start when the emote does
    not name them (`anonymous_add="first"`), or not at all (`None`). A failed
    reference tells only the sender.
    """
    case_sensitive = kwargs.pop("case_sensitive", True)
    fallback = kwargs.pop("fallback", None)
    try:
        emote, obj_mapping = parse_emote(
            sender, receivers, emote, case_sensitive=case_sensitive, fallback=fallback
        )
        emote, language_mapping = _rp.parse_language(sender, emote)
    except (_rp.EmoteError, _rp.LanguageError) as err:
        sender.msg(str(err))
        return

    skey = f"#{sender.id}"
    # we escape the object mappings since we'll do the language ones first
    emote = _rp._RE_REF.sub(r"{{#\1}}", emote)

    self_refs = [f"{skey}{ref}" for ref in ("t", "^", "v", "~", "")]
    if anonymous_add and not any(1 for tag in obj_mapping if tag in self_refs):
        # no self-reference in the emote - add it
        if anonymous_add == "first":
            # add case flag for initial caps
            skey += "t"
            # don't put a space after the self-ref if it's a possessive emote
            femote = "{key}{emote}" if emote.startswith("'") else "{key} {emote}"
        else:
            # add it to the end
            femote = "{emote} [{key}]"
        emote = femote.format(key="{{" + skey + "}}", emote=emote)
        obj_mapping[skey] = sender

    for receiver in receivers:
        # first handle the language mapping, which always produce different keys ##1
        if hasattr(receiver, "process_language") and callable(receiver.process_language):
            receiver_lang_mapping = {
                key: receiver.process_language(saytext, sender, langname)
                for key, (langname, saytext) in language_mapping.items()
            }
        else:
            receiver_lang_mapping = {
                key: saytext for key, (langname, saytext) in language_mapping.items()
            }
        # map the language {##num} markers. This will convert the escaped sdesc markers on
        # the form {{#num}} to {#num} markers ready to sdesc-map in the next step.
        sendemote = emote.format_map(receiver_lang_mapping)

        # map the ref keys to sdescs
        receiver_sdesc_mapping = dict(
            (
                ref,
                obj.get_display_name(receiver, ref=ref, noid=True),
            )
            for ref, obj in obj_mapping.items()
        )

        # do the template replacement of the sdesc/recog {#num} markers
        receiver.msg(
            text=(sendemote.format_map(receiver_sdesc_mapping), {"type": msg_type}),
            from_obj=sender,
            **kwargs,
        )


class CmdEmote(_ContribCmdEmote):
    __doc__ = _ContribCmdEmote.__doc__

    def func(self):
        """The contrib's emote (rpsystem.py:933-943), through send_emote above."""
        if not self.args:
            self.caller.msg("What do you want to do?")
            return
        emote = self.args
        targets = self.caller.location.contents if self.caller.location else [self.caller]
        if not emote.endswith((".", "?", "!", '"')):
            emote += "."
        send_emote(self.caller, targets, emote, anonymous_add="first")


class CmdSay(_ContribCmdSay):
    __doc__ = _ContribCmdSay.__doc__

    def func(self):
        """The contrib's say (rpsystem.py:962-971), through send_emote above."""
        caller = self.caller
        if not self.args:
            caller.msg("Say what?")
            return
        speech = caller.at_pre_say(self.args)
        targets = caller.location.contents if caller.location else [caller]
        send_emote(caller, targets, speech, msg_type="say", anonymous_add=None)


class CmdPose(_ContribCmdPose):
    """
    Set how others see you standing in a room.

    Usage:
      pose <pose>
      pose default <pose>
      pose reset

    Examples:
      pose is warming her hands by the fire
      pose is talking to /lanky

    The pose ends the sentence that starts with how others see you:
    *a lanky woman is warming her hands by the fire.* It stays in the room
    when you leave; you arrive anywhere else with your default pose
    (*is here.*). A /word names someone in the room as you see them now.

    See also: emote, say
    """

    def func(self):
        """
        The contrib's pose (rpsystem.py:1070-1122) with two changes (Names
        NM-T7): the references go through parse_emote, so a numbered one
        leaves no `/N`; and a reference that matches no one is the parser's
        line, not a traceback -- the contrib does not catch its EmoteError
        (run 2026-11-15).
        """
        caller = self.caller
        pose = self.args
        target = self.target
        if not pose and not self.reset:
            caller.msg("Usage: pose <pose-text> OR pose obj = <pose-text>")
            return

        if not pose.endswith((".", "?", "!", '"')):
            pose += "."
        if target:
            target = caller.search(target)
            if not target:
                return
            if not target.access(caller, "edit"):
                caller.msg("You can't pose that.")
                return
        else:
            target = caller

        target_name = target.sdesc.get() if hasattr(target, "sdesc") else target.key
        if not target.attributes.has("pose"):
            caller.msg(f"{target_name} cannot be posed.")
            return

        if self.reset:
            pose = target.db.pose_default
            target.db.pose = pose
        elif self.default:
            target.db.pose_default = pose
            caller.msg(f"Default pose is now '{target_name} {pose}'.")
            return
        else:
            # The references are mapped to short descriptions once, here.
            try:
                parsed, mapping = parse_emote(caller, caller.location.contents, pose)
            except EmoteError as err:
                caller.msg(str(err))
                return
            mapping = dict(
                (ref, obj.sdesc.get() if hasattr(obj, "sdesc") else obj.key)
                for ref, obj in mapping.items()
            )
            pose = parsed.format_map(mapping)

            if len(target_name) + len(pose) > 60:
                caller.msg(f"'{pose}' is too long.")
                return

            target.db.pose = pose

        caller.msg(f"Pose will read '{target_name} {pose}'.")



# -- who (NM-T14) ------------------------------------------------------------

_NUMBER_WORDS = (
    "no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty",
)


def abroad_line(count):
    """
    The sentence a player reads for `who` (Names UP14; NM-T14 lock 1 A).

    Args:
        count (int): connected accounts, the reader among them.

    Returns:
        str: *Seven travellers are abroad in the world.*, in words to twenty.
    """
    if count == 1:
        return "One traveller is abroad in the world."
    number = _NUMBER_WORDS[count] if 0 <= count < len(_NUMBER_WORDS) else str(count)
    return f"{number[:1].upper()}{number[1:]} travellers are abroad in the world."


class CmdWho(_EvenniaCmdWho):
    """
    see how many travellers are abroad

    Usage:
      who
      doing

    Tells you how many travellers are abroad in the world, yourself among
    them. Who they are, you learn in play. Staff (Builder and above) see the
    list of connected accounts.
    """

    def func(self):
        account = self.account
        if account and account.check_permstring("Builder"):
            return super().func()
        self.msg(abroad_line(evennia.SESSION_HANDLER.account_count()))
