"""Shared order status. Web and mobile read the same file.

The order never leaves the company: approve only changes the status.
Export to 1C stays a separate, human step on the web.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
ORDER_PATH = Path(os.environ.get("QOR_ORDER", ROOT / "data" / "order_state.json"))
WORKSPACE_PATH = Path(os.environ.get("QOR_OUT", ROOT / "data" / "workspace.json"))
ORDER_ID = "iek-current"

_lock = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_workspace() -> dict | None:
    if not WORKSPACE_PATH.is_file():
        return None
    return json.loads(WORKSPACE_PATH.read_text(encoding="utf-8"))


def _blank(as_of: str | None, status: str = "pending_approval") -> dict:
    return {
        "id": ORDER_ID,
        "status": status,
        "sentBy": "Айгерим",
        "sentAt": _now(),
        "decidedBy": None,
        "decidedAt": None,
        "comment": None,
        "asOf": as_of,
    }


def _read() -> dict | None:
    if not ORDER_PATH.is_file():
        return None
    return json.loads(ORDER_PATH.read_text(encoding="utf-8"))


def _write(state: dict) -> None:
    ORDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = ORDER_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ORDER_PATH)


def _ensure(as_of: str | None) -> dict:
    """Caller must hold _lock. Missing file starts as already sent for approval."""
    state = _read()
    if state is None:
        state = _blank(as_of, "pending_approval")
        _write(state)
        return state
    if as_of and state.get("asOf") is None:
        state["asOf"] = as_of
        _write(state)
    elif as_of and state.get("asOf") != as_of:
        state = _blank(as_of, "draft")
        _write(state)
    return state


def get_order(bundle: dict | None = None) -> dict:
    """Return the current order. A new 1C calculation (different asOf) drops back to draft."""
    as_of = None if bundle is None else bundle.get("asOf")
    with _lock:
        return _ensure(as_of)


def submit(actor_name: str, bundle: dict) -> dict:
    with _lock:
        state = _ensure(bundle.get("asOf"))
        if state["status"] not in ("draft", "returned"):
            raise ValueError("Отправить можно только черновик или заказ, возвращённый на доработку")
        state = {
            "id": ORDER_ID,
            "status": "pending_approval",
            "sentBy": actor_name,
            "sentAt": _now(),
            "decidedBy": None,
            "decidedAt": None,
            "comment": None,
            "asOf": bundle.get("asOf"),
        }
        _write(state)
        return state


def approve(actor_name: str) -> dict:
    with _lock:
        state = _ensure(None)
        if state["status"] != "pending_approval":
            raise ValueError("Утвердить можно только заказ на согласовании")
        state["status"] = "approved"
        state["decidedBy"] = actor_name
        state["decidedAt"] = _now()
        state["comment"] = None
        _write(state)
        return state


def return_order(actor_name: str, comment: str) -> dict:
    text = comment.strip()
    if not text:
        raise ValueError("Нужен комментарий, что исправить")
    with _lock:
        state = _ensure(None)
        if state["status"] != "pending_approval":
            raise ValueError("Вернуть можно только заказ на согласовании")
        state["status"] = "returned"
        state["decidedBy"] = actor_name
        state["decidedAt"] = _now()
        state["comment"] = text
        _write(state)
        return state
