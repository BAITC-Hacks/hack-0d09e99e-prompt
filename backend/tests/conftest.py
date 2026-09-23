"""Shared fixtures: the API runs against temp order/workspace files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qor.orders as orders  # noqa: E402
from main import app  # noqa: E402

AS_OF = "2026-09-01"


@pytest.fixture()
def state_paths(tmp_path, monkeypatch):
    order_path = tmp_path / "order_state.json"
    workspace_path = tmp_path / "workspace.json"
    workspace_path.write_text(
        json.dumps(
            {
                "asOf": AS_OF,
                "asOfLabel": "09.2026",
                "supplier": "IEK",
                "kpis": {"toOrder": 1, "critical": 1},
                "lines": [],
                "alerts": [],
                "anomalies": [],
                "series": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(orders, "ORDER_PATH", order_path)
    monkeypatch.setattr(orders, "WORKSPACE_PATH", workspace_path)
    return {"order": order_path, "workspace": workspace_path}


@pytest.fixture()
def client(state_paths) -> TestClient:
    return TestClient(app)


def login(client: TestClient, username: str, password: str) -> str:
    res = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["token"]


@pytest.fixture()
def buyer_token(client) -> str:
    return login(client, "aigerim", "buyer")


@pytest.fixture()
def director_token(client) -> str:
    return login(client, "daniyar", "director")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
