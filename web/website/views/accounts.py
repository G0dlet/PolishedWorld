"""
Website account views: PolishedWorld's override of Evennia's registration.

Evennia 6.1.0's ``AccountCreateView.form_valid``
(``evennia/web/website/views/accounts.py:43-70``) creates an account without
reading ``NEW_ACCOUNT_REGISTRATION_ENABLED``; only the template hides the form
(``register.html:30``). A POST to ``/auth/register`` therefore creates an
account even with the setting off. The view below gates on the setting, so
that one setting is the single knob for every door a player could use
(Launch Minimum LM4, task L1.2).

Why a gated subclass and not a dropped route:

* Evennia's ``login.html:41`` reverses ``{% url 'register' %}`` with no
  ``register_enabled`` guard, so the name ``register`` must keep resolving or
  the login page fails with ``NoReverseMatch``.
* ``web/urls.py`` appends Evennia's own root patterns, which include the
  ungated ``auth/register`` a second time; a route merely filtered out of
  ``web/website/urls.py`` would fall through to that copy and stay open.
  The gated route is listed first there, and Django serves the first match.
"""

from django.conf import settings
from django.http import Http404

from evennia.web.website.views.accounts import AccountCreateView


class GatedAccountCreateView(AccountCreateView):
    """``AccountCreateView`` that answers 404 while registration is closed."""

    def dispatch(self, request, *args, **kwargs):
        # Read per request, not at import, so override_settings in tests and a
        # settings change after `evennia reboot` both take effect.
        if not settings.NEW_ACCOUNT_REGISTRATION_ENABLED:
            raise Http404("Registration is closed.")
        return super().dispatch(request, *args, **kwargs)
