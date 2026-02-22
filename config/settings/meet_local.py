"""Local mode settings overlay for Meet - disables HTTPS requirements."""
from meet.settings import *  # noqa: F401,F403
from meet.settings import Production as _Production


class Local(_Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_REDIRECT_URL = "/"
    LOGIN_REDIRECT_URL_FAILURE = "/"
