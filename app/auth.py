import base64
import hashlib
import hmac
import json
import time

from fastapi import Request

from app.config import settings
from app.exceptions import AppException


COOKIE_NAME = "snip_admin_session"
SESSION_LIFETIME_SECONDS = 60 * 60 * 12


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _sign(payload: str) -> str:
    return hmac.new(
        settings.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def create_session_token() -> str:
    payload = _encode(json.dumps({"exp": int(time.time()) + SESSION_LIFETIME_SECONDS}).encode())
    return f"{payload}.{_sign(payload)}"


def is_valid_session(token: str | None) -> bool:
    if not token:
        return False
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            return False
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded))
        return int(data["exp"]) > int(time.time())
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


def password_is_valid(password: str) -> bool:
    return hmac.compare_digest(password, settings.ADMIN_PASSWORD)


def require_admin(request: Request) -> None:
    if not is_valid_session(request.cookies.get(COOKIE_NAME)):
        raise AppException(status_code=401, message="Owner authentication required")
