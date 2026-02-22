"""Settings overlay for Messages - disables HTTPS requirements for Caddy termination."""
import os
from configurations import values
from messages.settings import Production as _Production


class Local(_Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    ALLOWED_HOSTS = ["*"]
    CSRF_TRUSTED_ORIGINS = values.ListValue(
        [os.environ.get("MESSAGES_URL", "http://localhost:9124")]
    )
    LOGIN_REDIRECT_URL = values.Value(
        "/", environ_name="LOGIN_REDIRECT_URL", environ_prefix=None
    )
    LOGIN_REDIRECT_URL_FAILURE = values.Value(
        "/", environ_name="LOGIN_REDIRECT_URL_FAILURE", environ_prefix=None
    )
