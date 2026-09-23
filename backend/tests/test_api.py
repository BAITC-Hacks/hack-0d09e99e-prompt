"""API tests through the FastAPI TestClient: auth, roles, order transitions."""

from __future__ import annotations

from conftest import auth


def test_health_reports_the_live_model(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["model"] == "demand_model_v2.cbm"
    assert body["ready"] is True


def test_login_wrong_password(client):
    res = client.post("/v1/auth/login", json={"username": "aigerim", "password": "nope"})
    assert res.status_code == 401


def test_login_returns_public_user(client):
    res = client.post("/v1/auth/login", json={"username": "daniyar", "password": "director"})
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "director"
    assert body["name"] == "Данияр"
    assert "password" not in body
    assert body["token"]


def test_me_requires_a_token(client):
    assert client.get("/v1/me").status_code == 401


def test_me_with_token(client, buyer_token):
    res = client.get("/v1/me", headers=auth(buyer_token))
    assert res.status_code == 200
    assert res.json()["username"] == "aigerim"


def test_order_defaults_to_draft(client, buyer_token):
    res = client.get("/v1/orders/current", headers=auth(buyer_token))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "draft"
    assert body["sentBy"] is None
    assert "asOf" not in body  # внутреннее поле наружу не отдаём


def test_submit_then_conflict(client, buyer_token):
    res = client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    assert res.status_code == 200
    assert res.json()["status"] == "pending_approval"
    assert res.json()["sentBy"] == "Айгерим"
    again = client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    assert again.status_code == 409


def test_director_cannot_submit(client, director_token):
    res = client.post("/v1/orders/iek-current/submit", headers=auth(director_token))
    assert res.status_code == 403


def test_buyer_cannot_approve(client, buyer_token):
    client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    res = client.post("/v1/orders/iek-current/approve", headers=auth(buyer_token))
    assert res.status_code == 403


def test_director_approves(client, buyer_token, director_token):
    client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    res = client.post("/v1/orders/iek-current/approve", headers=auth(director_token))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "approved"
    assert body["decidedBy"] == "Данияр"


def test_director_returns_with_comment(client, buyer_token, director_token):
    client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    res = client.post(
        "/v1/orders/iek-current/return",
        headers=auth(director_token),
        json={"comment": "проверь количество по трубам"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "returned"
    assert res.json()["comment"] == "проверь количество по трубам"


def test_return_without_comment_is_422(client, buyer_token, director_token):
    client.post("/v1/orders/iek-current/submit", headers=auth(buyer_token))
    res = client.post("/v1/orders/iek-current/return", headers=auth(director_token), json={"comment": ""})
    assert res.status_code == 422


def test_unknown_order_is_404(client, buyer_token):
    res = client.post("/v1/orders/unknown/submit", headers=auth(buyer_token))
    assert res.status_code == 404


def test_ask_unknown_sku_is_404(client, buyer_token):
    res = client.post("/v1/sku/NOPE/ask", headers=auth(buyer_token), json={"question": "почему?"})
    assert res.status_code == 404


def test_bundle_requires_auth(client, buyer_token):
    assert client.get("/v1/bundle").status_code == 401
    res = client.get("/v1/bundle", headers=auth(buyer_token))
    assert res.status_code == 200
    assert res.json()["asOf"] == "2026-09-01"
