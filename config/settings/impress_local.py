"""Local mode settings overlay for Docs - disables HTTPS requirements."""
from impress.settings import *  # noqa: F401,F403
from impress.settings import Production as _Production


class Local(_Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_REDIRECT_URL = "/"
