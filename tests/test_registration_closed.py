"""
Registration is closed at every door (Launch Minimum L1.2, LM4).

A player can try to make an account three ways in Evennia 6.1.0:

1. the menu login the project runs (``CMDSET_UNLOGGEDIN`` is menu_login's
   cmdset; the gate is ``menu_login.py:93``);
2. the telnet ``create`` command (``unloggedin.py:178``), which that cmdset
   does not install;
3. the website's ``/auth/register``, whose Evennia view does not read the
   setting at all; ``web/website/views/accounts.py`` gates it.

Each door has a "closed" test and, where the door exists, an
``override_settings(True)`` positive control: a test that a closed door
refuses is only worth something if the same test sees the door open when the
setting says so (otherwise a broken URL or a crashing node would also pass).
"""

from unittest.mock import MagicMock

from django.conf import settings
from django.test import override_settings
from django.urls import resolve, reverse

from evennia.accounts.models import AccountDB
from evennia.contrib.base_systems.menu_login import menu_login
from evennia.utils.test_resources import EvenniaTest
from evennia.utils.utils import class_from_module

from web.website.views.accounts import GatedAccountCreateView

NEW_NAME = "Newcomer"
# Passes Evennia's validators: only [\w. @+\-',], at least 8 characters,
# not common, not all digits, not similar to the username.
PASSWORD = "Juniper-Lantern.42"
FORM = {
    "username": NEW_NAME,
    "email": "",
    "password1": PASSWORD,
    "password2": PASSWORD,
}


def _account_exists(name):
    return AccountDB.objects.filter(username__iexact=name).exists()


class TestTheKnob(EvenniaTest):
    """The shipped value. Pressured by LM-M2."""

    def test_registration_setting_is_off(self):
        self.assertFalse(settings.NEW_ACCOUNT_REGISTRATION_ENABLED)


class TestWebDoor(EvenniaTest):
    """Door 3, the one Evennia leaves open. Pressured by LM-M1, LM-M1b, LM-M2."""

    def test_route_resolves_to_gated_view(self):
        # First match wins; Evennia's ungated copy is further down the list.
        match = resolve("/auth/register")
        self.assertIs(match.func.view_class, GatedAccountCreateView)

    def test_get_register_is_404(self):
        self.assertEqual(self.client.get("/auth/register").status_code, 404)

    def test_post_register_is_404_and_creates_nothing(self):
        response = self.client.post("/auth/register", FORM)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(_account_exists(NEW_NAME))

    @override_settings(NEW_ACCOUNT_REGISTRATION_ENABLED=True)
    def test_post_register_creates_when_enabled(self):
        # Positive control: the same POST does create an account (and
        # redirects to login) when the setting is on, so the 404 above is the
        # gate and not a mistyped URL or an invalid form.
        response = self.client.post("/auth/register", FORM)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(_account_exists(NEW_NAME))

    def test_login_page_still_renders(self):
        # login.html:41 reverses 'register' unguarded; the page must not 500.
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)


class TestMenuDoor(EvenniaTest):
    """Door 1, the live telnet door. Pressured by LM-M2."""

    def _username_check(self):
        """The menu's ``_default`` goto, i.e. what runs on a typed name."""
        caller = MagicMock()
        _text, options = menu_login.node_enter_username(caller, "")
        check = next(opt["goto"] for opt in options if opt["key"] == "_default")
        return caller, check

    def test_new_name_is_refused(self):
        caller, check = self._username_check()
        self.assertIsNone(check(caller, NEW_NAME))
        caller.msg.assert_any_call("Registration is currently disabled.")
        self.assertFalse(_account_exists(NEW_NAME))

    @override_settings(NEW_ACCOUNT_REGISTRATION_ENABLED=True)
    def test_new_name_proceeds_when_enabled(self):
        caller, check = self._username_check()
        node, kwargs = check(caller, NEW_NAME)
        self.assertEqual(node, "node_enter_password")
        self.assertTrue(kwargs["new_user"])

    def test_existing_account_still_reaches_password(self):
        # Closing registration must not lock out the staff-made accounts.
        caller, check = self._username_check()
        node, kwargs = check(caller, self.account.username)
        self.assertEqual(node, "node_enter_password")
        self.assertFalse(kwargs["new_user"])


class TestTelnetCreateNotInstalled(EvenniaTest):
    """Door 2 is dead here; this keeps it dead if CMDSET_UNLOGGEDIN changes."""

    def test_unloggedin_cmdset_has_no_create(self):
        cmdset = class_from_module(settings.CMDSET_UNLOGGEDIN)()
        names = {name for cmd in cmdset.commands for name in (cmd.key, *cmd.aliases)}
        self.assertNotIn("create", names)
