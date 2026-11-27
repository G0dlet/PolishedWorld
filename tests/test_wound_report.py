"""
`status` names the wounds: under the health line, `status` and `sheet` say
where a body is badly hurt and what state each location is in; the health
figure reads out of 100. Wounds, Task WN-T11
(docs/PolishedWorld_Wounds_Decomposition.md; Combat Design §4.4, WN2, WN11,
OQ-WN8 answered (a); OQ-WN5's words).

The fixture's char1 is set to CON 10, SIZ 11, POW 11 -- CON + SIZ 21, the
decomposition's numbers: head 5, chest 7, abdomen 6, arms 4, legs 5, and a
limb's clock of 1260 s. `world.wounds._now` and `world.wounds.delay` are
patched as in tests/test_wound_clocks.py.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestReport`: an unhurt body has no line. Five points of starvation put
  the head, both arms and both legs at a Serious Wound -- five lines, in
  `body.LOCATIONS`' order -- and the chest and abdomen, Minor, are not
  listed (WNM42: Minor Wounds listed). **A maimed leg after a respawn is
  listed though it is unhurt** (red: `status` read 100 % and said nothing of
  it; WNM43: the state left out). Two blows, the leg first and the head
  second, are listed head first, whatever order the stored damage keeps
  (WNM44: the order taken from the stored dict). A lost test on a limb reads
  *useless*. A clock reads *bleeding out* and the whole minutes left, a
  vital one *under a minute*.
- `TestTheFigure`: the health figure is out of 100, the percentage rounded
  down, so 100 means unhurt and 0 a Major Wound (WNM44b: rounded to the
  nearest, an arm at 7/8 reads 88); `status`, `sheet` and the `char`
  snapshot read it the same; the word at 0 % is *grievously wounded*, which
  a living body can read.
- `TestTheScreens`: `status` and `sheet` print the lines under the health
  line, and nothing for a body with only Minor Wounds. **A maimed leg after
  a respawn reads 100/100 and its line** -- the decomposition's red: on
  WN-T10's code `status` read 100 % and said nothing of it.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_report
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaCommandTest

from commands.character_commands import CmdSheet, CmdStatus
from tests.test_wound_states import MADE, LOSE, ROLL, WIN
from world import client_state, hero_points, wounds

NOW = 1_000_000.0


class _Report(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.stats.con.base = 10
        self.char1.stats.siz.base = 11
        self.char1.stats.pow.base = 11
        self.char1.traits.fatigue.current = 100
        self.char1.db.respawn_location = self.room2
        # Glancing Blow off: these tests drive Major Wounds, and a body with
        # Hero Points would have each one trimmed to a Serious Wound (HE1;
        # Hero Points decomposition §4, P1, and HE-T5).
        hero_points.set_glancing(self.char1, False)
        clock = mock.patch("world.wounds._now")
        self.now = clock.start()
        self.now.return_value = NOW
        alarm = mock.patch("world.wounds.delay")
        alarm.start()
        slot = mock.patch("world.timed_actions.delay")
        slot.start()
        for patcher in (clock, alarm, slot):
            self.addCleanup(patcher.stop)

    def at(self, seconds):
        self.now.return_value = NOW + seconds

    def blow(self, amount, location, made=MADE, roll=WIN):
        with mock.patch(ROLL, return_value=roll), mock.patch.object(self.char1, "msg"):
            self.char1.apply_health_damage(amount, location=location, made=made)

    def starve(self, points):
        self.char1.apply_health_damage(points, location=wounds.ALL)

    def report(self):
        return wounds.report(self.char1)


class TestReport(_Report):
    def test_an_unhurt_body_has_no_line(self):
        self.assertEqual(self.report(), [])

    def test_five_points_of_starvation_list_head_arms_and_legs_in_order(self):
        self.starve(5)
        self.assertEqual(self.report(), [
            "head         0/5  serious wound",
            "right arm    0/4  serious wound",
            "left arm     0/4  serious wound",
            "right leg    0/5  serious wound",
            "left leg     0/5  serious wound",
        ])

    def test_a_maimed_leg_after_a_respawn_is_listed_though_unhurt(self):
        self.blow(10, "left_leg")               # leg 5: -5, Major, won: maimed
        self.char1.at_character_death(killer="test")
        self.assertIsNone(self.char1.attributes.get("body_damage"))
        self.assertEqual(self.report(), ["left leg     5/5  maimed"])

    def test_the_order_is_the_bodys_not_the_stored_damages(self):
        self.blow(5, "left_leg", made=None)     # stored first
        self.blow(5, "head", made=None)
        self.assertEqual(list(self.char1.db.body_damage), ["left_leg", "head"])
        self.assertEqual(self.report(), [
            "head         0/5  serious wound",
            "left leg     0/5  serious wound",
        ])

    def test_a_lost_test_on_a_limb_reads_useless(self):
        self.blow(5, "left_arm", roll=LOSE)     # arm 4: -1, Serious, lost
        self.assertEqual(self.report(), ["left arm    -1/4  serious wound, useless"])

    def test_a_limbs_clock_reads_whole_minutes_left(self):
        self.blow(8, "left_arm")                # arm 4: -4, Major, won
        self.assertEqual(self.report(),
                         ["left arm    -4/4  major wound, maimed, bleeding out (21 min)"])
        self.at(60.5)                           # 19.99 minutes left
        self.assertEqual(self.report(),
                         ["left arm    -4/4  major wound, maimed, bleeding out (19 min)"])

    def test_a_vital_clock_reads_under_a_minute(self):
        self.blow(10, "head")                   # head 5: -5, Major, won
        self.assertEqual(self.report(),
                         ["head        -5/5  major wound, maimed, bleeding out (under a minute)"])


class TestTheFigure(_Report):
    def test_out_of_100_rounded_down(self):
        self.starve(1)                          # an arm at 7/8: 87.5 %
        self.assertEqual(wounds.health_shown(self.char1), (87, 100, 87.5))
        self.assertEqual(client_state.char_snapshot(self.char1)["health"],
                         {"current": 87, "max": 100, "desc": "bruised"})

    def test_five_points_read_50_of_100_on_every_screen(self):
        self.starve(5)
        self.assertEqual(client_state.char_snapshot(self.char1)["health"],
                         {"current": 50, "max": 100, "desc": "badly hurt"})
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertIn("Health:   50/100 ( 50.0%) - badly hurt", out)
        out = self.call(CmdSheet(), "", caller=self.char1)
        self.assertIn("Health          50/100 ( 50.0%) - badly hurt", out)

    def test_unhurt_is_100_and_a_major_wound_is_0_grievously_wounded(self):
        self.assertEqual(wounds.health_shown(self.char1)[:2], (100, 100))
        self.blow(10, "head")                   # survived: alive at 0 %
        self.assertEqual(wounds.health_shown(self.char1)[:2], (0, 100))
        self.assertEqual(self.char1.health_desc(), "grievously wounded")

    def test_an_object_with_no_body_reads_none(self):
        self.assertIsNone(wounds.health_shown(self.obj1))


class TestTheScreens(_Report):
    def test_status_lists_the_wounds_under_the_health_line(self):
        self.starve(5)
        out = self.call(CmdStatus(), "", caller=self.char1)
        lines = out.splitlines()
        health = next(i for i, line in enumerate(lines) if "Health:" in line)
        self.assertIn("head         0/5  serious wound", lines[health + 1])
        self.assertIn("left leg     0/5  serious wound", lines[health + 5])
        self.assertIn("Hunger:", lines[health + 6])

    def test_a_maimed_leg_after_a_respawn_shows_in_status_at_100(self):
        self.blow(10, "left_leg")
        self.char1.at_character_death(killer="test")
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertIn("left leg     5/5  maimed", out)
        self.assertIn("Health:  100/100 (100.0%) - healthy", out)

    def test_sheet_lists_them_too(self):
        self.blow(5, "left_arm", roll=LOSE)
        out = self.call(CmdSheet(), "", caller=self.char1)
        self.assertIn("left arm    -1/4  serious wound, useless", out)

    def test_only_minor_wounds_add_nothing(self):
        self.starve(1)
        out = self.call(CmdStatus(), "", caller=self.char1)
        lines = out.splitlines()
        health = next(i for i, line in enumerate(lines) if "Health:" in line)
        self.assertIn("Hunger:", lines[health + 1])
