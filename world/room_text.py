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
