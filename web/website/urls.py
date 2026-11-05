"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns

from web.website.views.accounts import GatedAccountCreateView
from web.website.views.board import BoardView

# add patterns here
urlpatterns = [
    # Registration, gated on NEW_ACCOUNT_REGISTRATION_ENABLED (Launch Minimum
    # L1.2). Evennia's view does not read the setting (views/accounts.py:43-70).
    # Listed first so it wins: Django serves the first match, and Evennia's
    # ungated auth/register follows below and again in web/urls.py. Same path
    # and name, so {% url 'register' %} in Evennia's login.html still reverses.
    path("auth/register", GatedAccountCreateView.as_view(), name="register"),
    # The public dev board, read-only, no login (BACKLOG *Public dev board*).
    path("board/", BoardView.as_view(), name="board"),
]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns
