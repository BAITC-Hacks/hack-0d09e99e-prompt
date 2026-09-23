"""Unit tests for the HMAC demo login in qor.auth."""

from __future__ import annotations

import hashlib
import hmac
import json

from qor import auth


def test_authenticate_ok():
    user = auth.authenticate("aigerim", "buyer")
    assert user is not None
    assert user["role"] == "buyer"


def test_authenticate_wrong_password():
    assert auth.authenticate("aigerim", "wrong") is None


def test_authenticate_unknown_user():
    assert auth.authenticate("nobody", "buyer") is None


def test_username_is_normalized():
    assert auth.authenticate("  Aigerim ", "buyer") is not None


def test_token_roundtrip():
    user = auth.authenticate("daniyar", "director")
    token = auth.issue_token(user)
    back = auth.verify_token(token)
    assert back is not None
    assert back["username"] == "daniyar"
    assert back["role"] == "director"


def test_tampered_signature_rejected():
    token = auth.issue_token(auth.authenticate("aigerim", "buyer"))
    body, sig = token.split(".")
    flipped = ("0" if sig[-1] != "0" else "1")
    assert auth.verify_token(f"{body}.{sig[:-1]}{flipped}") is None


def test_expired_token_rejected():
    user = auth.authenticate("aigerim", "buyer")
    token = auth.issue_token(user, now=1_000)
    assert auth.verify_token(token, now=1_000 + auth.TTL_SECONDS + 10) is None


def test_forged_role_rejected():
    """A correctly signed token with a role the user does not have must fail."""
    body = auth._b64(json.dumps({"sub": "aigerim", "role": "director", "name": "X", "exp": 9_999_999_999}).encode())
    sig = hmac.new(auth.SECRET, body.encode(), hashlib.sha256).hexdigest()
    assert auth.verify_token(f"{body}.{sig}") is None


def test_malformed_token_rejected():
    assert auth.verify_token("not-a-token") is None
    assert auth.verify_token("") is None
