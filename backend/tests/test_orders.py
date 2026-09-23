"""Unit tests for the order status machine in qor.orders.

Nothing here touches the real data/ files — conftest points the module at tmp paths.
"""

from __future__ import annotations

import pytest

import qor.orders as orders
from conftest import AS_OF


def bundle(as_of: str = AS_OF) -> dict:
    return {"asOf": as_of}


def test_missing_file_is_a_draft(state_paths):
    state = orders.get_order(bundle())
    assert state["status"] == "draft"
    assert state["sentBy"] is None
    assert state["asOf"] == AS_OF


def test_submit_from_draft(state_paths):
    state = orders.submit("Айгерим", bundle())
    assert state["status"] == "pending_approval"
    assert state["sentBy"] == "Айгерим"
    assert state["sentAt"]


def test_double_submit_rejected(state_paths):
    orders.submit("Айгерим", bundle())
    with pytest.raises(ValueError):
        orders.submit("Айгерим", bundle())


def test_approve_only_from_pending(state_paths):
    with pytest.raises(ValueError):
        orders.approve("Данияр")
    orders.submit("Айгерим", bundle())
    state = orders.approve("Данияр")
    assert state["status"] == "approved"
    assert state["decidedBy"] == "Данияр"


def test_return_needs_a_comment(state_paths):
    orders.submit("Айгерим", bundle())
    with pytest.raises(ValueError):
        orders.return_order("Данияр", "   ")


def test_return_then_resubmit(state_paths):
    orders.submit("Айгерим", bundle())
    state = orders.return_order("Данияр", "проверь количество")
    assert state["status"] == "returned"
    assert state["comment"] == "проверь количество"
    again = orders.submit("Айгерим", bundle())
    assert again["status"] == "pending_approval"
    assert again["comment"] is None


def test_new_calculation_drops_back_to_draft(state_paths):
    orders.submit("Айгерим", bundle("2026-09-01"))
    state = orders.get_order(bundle("2026-10-01"))
    assert state["status"] == "draft"
    assert state["asOf"] == "2026-10-01"


def test_approve_after_return_rejected(state_paths):
    orders.submit("Айгерим", bundle())
    orders.return_order("Данияр", "поправь")
    with pytest.raises(ValueError):
        orders.approve("Данияр")
