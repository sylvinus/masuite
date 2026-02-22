"""Local mode settings overlay for Drive - disables HTTPS requirements."""
from drive.settings import *  # noqa: F401,F403
from drive.settings import Production as _Production


class Local(_Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_REDIRECT_URL = "/"
