"""Demo login for the two roles in docs/07-roles-and-screens.md.

Buyer (менеджер закупа) submits an order. Director (руководитель) approves or
returns it. Tokens are HMAC-signed and carry no client data.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

SECRET = os.environ.get("QOR_AUTH_SECRET", "qor-dev-secret").encode()
TTL_SECONDS = int(os.environ.get("QOR_TOKEN_TTL_SECONDS", str(7 * 24 * 3600)))

# Demo accounts. Override passwords with QOR_BUYER_PASSWORD / QOR_DIRECTOR_PASSWORD.
USERS: dict[str, dict[str, str]] = {
    "aigerim": {
        "username": "aigerim",
        "password": os.environ.get("QOR_BUYER_PASSWORD", "buyer"),
        "role": "buyer",
        "name": "Айгерим",
        "title": "Менеджер закупа",
    },
    "daniyar": {
        "username": "daniyar",
        "password": os.environ.get("QOR_DIRECTOR_PASSWORD", "director"),
        "role": "director",
        "name": "Данияр",
        "title": "Руководитель",
    },
}


def public_user(user: dict[str, str]) -> dict[str, str]:
    return {
        "username": user["username"],
        "role": user["role"],
        "name": user["name"],
        "title": user["title"],
    }


def authenticate(username: str, password: str) -> dict[str, str] | None:
    user = USERS.get(username.strip().lower())
    if user is None:
        return None
    if not hmac.compare_digest(user["password"], password):
        return None
    return user


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def issue_token(user: dict[str, str], now: float | None = None) -> str:
    issued = int(now if now is not None else time.time())
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["name"],
        "exp": issued + TTL_SECONDS,
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_token(token: str, now: float | None = None) -> dict[str, Any] | None:
    body, dot, sig = token.partition(".")
    if not dot or not body or not sig:
        return None
    expected = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(now if now is not None else time.time()):
        return None
    user = USERS.get(str(payload.get("sub", "")))
    if user is None or user["role"] != payload.get("role"):
        return None
    return public_user(user)
