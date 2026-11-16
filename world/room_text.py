"""
world/room_text.py
==================
A room look in two text messages (webclient decomposition W5.4, WC4).

Until W5.4 a look at the room you stand in was one message, `type: "look"`
(evennia/contrib/grid/extended_room/extended_room.py:632, and
DefaultCharacter's at_post_move and at_post_puppet, objects.py:3236 and
:3281). `room_look` sends the same text as two messages, in order:

  1. the description -- name, desc -- as `type: "look"`;
  2. the exits, characters and things as `type: "room_contents"`, but only
     when there is at least one (lock 2A): an empty second message would be
     a blank line in a telnet client and an empty line in the webclient.

Joined with a newline the two are exactly the old message: Evennia's
`format_appearance` collapses runs of newlines to one and strips the ends
(objects.py:1864-1876, `compress_whitespace(max_linebreaks=1)`), so cutting
the appearance template between `{desc}` and `{exits}` and formatting each
half the same way loses and adds nothing. The template's header and footer
are empty for the project's Room; a footer would move from after the lists
to the end of the first message. A telnet session sees the same lines; the
one byte-level difference is the colour reset the portal appends to every
message (telnet.py send_text), now also at the end of the first.

The webclient hides `room_contents` only when the location panel shows the
same lists (web/static/polishedworld/js/pw_text.js, WC4); every other client
shows both, so no session ever loses a line (WC1).

Three callers use `room_look` (lock 1A): the `look` command with no argument
(commands/world_commands.py CmdRoomLook, lock 3A), `Character.at_post_move`
and `Character.at_post_puppet` (typeclasses/characters.py), which no longer
pass up to DefaultCharacter's hooks. Looking at anything else -- an object,
`look here` -- is unchanged: one message, lists included.

`room_lists` is the one place the room's lists are chosen (lock 4C): the
Room's display hooks (typeclasses/rooms.py) format them for look, and the
webclient's room snapshot (world/client_state.py) sends them as data.
`character_line` is the one line an awake character gets in look (Names
NM-T8): a line each, with its pose; `character_parts` is the same line in
two parts for the snapshot, the pose left out when it is *is here.* (NM-T17).
"""

from django.conf import settings
from evennia.utils.utils import inherits_from

# The kwarg the Room's three list hooks read: `room_lists=False` makes them
# return "", so return_appearance renders the description alone. Passed
# through at_look, which hands its kwargs to every display hook.
LISTS_KWARG = "room_lists"


def numbered_names(objs, viewer, **kwargs):
    """
    Display strings for `objs` as `viewer` sees them: grouped by display
    name and numbered as DefaultObject.get_display_things does ("two
    stones"), sorted by name. The one grouping both the room's things (look
    and the room panel) and the inventory panel (W7.1 lock 2) read.

    Args:
        objs (iterable): the objects to name.
        viewer (Object): whose display names are asked for.
        **kwargs: passed on to `get_display_name`.

    Returns:
        list[str]: one string per name, "a stone" or "two stones".
    """
    grouped = {}
    for obj in objs:
        grouped.setdefault(obj.get_display_name(viewer, **kwargs), []).append(obj)
    names = []
    for name, group in sorted(grouped.items()):
        singular, plural = group[0].get_numbered_name(len(group), viewer, key=name)
        names.append(singular if len(group) == 1 else plural)
    return names


def character_line(char, viewer, **kwargs):
    """
    The room's line for one awake character, as `viewer` reads it (Names K8,
    NM14; NM-T8): the name with its pose, *A broad-shouldered man is here.*

    The name is asked for with `ref="t"`, as an emote's `/Tall` and a
    whisper ask for one at the start of a line: the first character up, the
    rest as written, as `$You()` writes it (`Character.process_sdesc`,
    `process_recog`; NM-T9 lock 1B, which replaced NM-T8's 2A). The pose is
    the contrib's (`get_posed_sdesc`, rpsystem.py:1366): the current one,
    else the default. A caller's own `pose` or `ref` does not reach the call
    twice.

    Args:
        char (Object): an awake character, from `room_lists(...)["characters"]`.
        viewer (Object): who reads the line.
        **kwargs: passed on to `get_display_name`.

    Returns:
        str: the line, with no colour of its own.
    """
    return char.get_display_name(viewer, **{**kwargs, "pose": True, "ref": "t"})


# The contrib's default pose (rpsystem.py:1566, backfilled by NM-T4): it says
# nothing a list of the people present does not, so the panel leaves it out.
DEFAULT_POSE = "is here."


def character_parts(char, viewer, **kwargs):
    """
    The room's line for one awake character in two parts, for the webclient's
    location panel (Names NM-T17 lock 2b, which replaced NM-T8's lock 1B):
    the name on its row, the pose under it.

    The name is `character_line`'s without the pose, so whenever the pose is
    shown, `name + " " + pose` is look's line. The pose is the one look shows
    (`get_posed_sdesc`: the current one, else the default), or `""` when that
    is the contrib's *is here.* -- a character's own default pose is shown,
    as look shows it. `look` itself keeps *is here.* (K8).

    Args:
        char (Object): an awake character, from `room_lists(...)["characters"]`.
        viewer (Object): who reads the line.
        **kwargs: passed on to `get_display_name`.

    Returns:
        tuple[str, str]: `(name, pose)`, with no colour of their own.
    """
    name = char.get_display_name(viewer, **{**kwargs, "pose": False, "ref": "t"})
    pose = char.db.pose or char.db.pose_default or ""
    return name, ("" if pose == DEFAULT_POSE else pose)


def room_lists(room, viewer, **kwargs):
    """
    The room's lists as look shows them to `viewer`.

    Args:
        room (Room): the room looked at.
        viewer (Object): who looks; never listed, and display names and the
            view lock are read for them.
        **kwargs: passed on to `filter_visible` and `get_display_name`, as
            Evennia's own display hooks pass theirs.

    Returns:
        dict: `exits` -- visible exit objects (the order Evennia's
        get_display_exits sorts further with `exit_order`); `characters` --
        awake characters other than the viewer that the viewer may view;
        `things` -- display strings for other visible objects, grouped by
        name and numbered as DefaultObject.get_display_things does
        ("two stones"), sorted by name; `statues` -- characters of logged-out
        accounts (WC14), which look lists after the things.
    """
    exits = room.filter_visible(room.contents_get(content_type="exit"), viewer, **kwargs)
    characters, statues = [], []
    for obj in room.contents_get(content_type="character"):
        if obj == viewer or not obj.access(viewer, "view"):
            continue
        (statues if getattr(obj, "is_statue", False) else characters).append(obj)
    things = numbered_names(
        room.filter_visible(room.contents_get(content_type="object"), viewer, **kwargs),
        viewer, **kwargs)
    return {"exits": exits, "characters": characters, "things": things, "statues": statues}


def contents_text(room, viewer):
    """
    The room's lists as the second message carries them: what the appearance
    template's `{exits}`, `{characters}` and `{things}` lines render to,
    formatted as `return_appearance` formats the whole. "" when all three
    are empty.
    """
    lines = "\n".join((
        room.get_display_exits(viewer),
        room.get_display_characters(viewer),
        room.get_display_things(viewer),
    ))
    return room.format_appearance(lines, viewer)


def room_look(char, room, session=None):
    """
    Send `char` a look at `room` as `look` + `room_contents` (WC4).

    A location that is not a project Room (no list hooks that honour
    LISTS_KWARG), or one `char` may not view, gets the single message
    `at_look` makes, as before. Never raises for a missing room: `None`
    sends nothing, since at_post_move must not raise (objects.py:1331).

    Args:
        char (Object): the looker; the messages go to its sessions.
        room (Object or None): what is looked at.
        session (Session, optional): only this session, as the look command
            sends to the session that typed it; all of char's otherwise.
    """
    if room is None:
        return
    if not inherits_from(room, settings.BASE_ROOM_TYPECLASS) or not room.access(char, "view"):
        char.msg(text=(char.at_look(room), {"type": "look"}), session=session)
        return
    description = char.at_look(room, **{LISTS_KWARG: False})
    lists = contents_text(room, char)
    char.msg(text=(description, {"type": "look"}), session=session)
    if lists:
        char.msg(text=(lists, {"type": "room_contents"}), session=session)
