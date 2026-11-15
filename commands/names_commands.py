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

A statue hears nothing: its player is not there. The lines are written out
with singular *they* (as `typeclasses/characters.py:539`), not `$pron()`:
Evennia's neutral pronoun is *it*, and no character has a gender yet.

MULTIPLAYER
-----------
A recog is written only on its owner, by its owner's command (Names UG6):
two players recognising the same person write two different Attributes, and
nothing ticks. The push to the webclient is NM-T17's.
"""

import re

from django.conf import settings
from evennia import Command
from evennia.contrib.rpg.rpsystem.rpsystem import RecogError, SdescError
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
                    "$You() introduces themselves as {truename}.",
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
                    "$You() introduces themselves to you as {truename}.",
                    exclude=[obj for obj in location.contents if obj != target],
                    from_obj=caller,
                    mapping=mapping,
                )
                location.msg_contents(
                    "$You() introduces themselves to {target}.",
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
