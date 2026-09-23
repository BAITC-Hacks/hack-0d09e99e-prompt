"""Qor API for the web upload and the Flutter approval app.

Roles: buyer submits, director approves or returns. Nothing is sent to a supplier.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from qor.auth import authenticate, issue_token, public_user, verify_token
from qor.contract import MODEL_NAME
from qor.explain import answer, find_line
from qor.orders import ORDER_ID, approve, get_order, load_workspace, return_order, submit
from qor.pipeline import MODEL_PATH, build_workspace

app = FastAPI(
    title="Qor",
    version="0.2.0",
    description="Расчёт заказов и согласование. Поставщику заказ сам не уходит.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
_bearer = HTTPBearer(auto_error=False)


class LoginIn(BaseModel):
    username: str
    password: str


class CommentIn(BaseModel):
    comment: str = Field(min_length=1)


class AskIn(BaseModel):
    question: str = Field(min_length=1)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        raise HTTPException(status_code=401, detail="Нужен заголовок Authorization: Bearer <token>")
    user = verify_token(creds.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Токен недействителен или истёк")
    return user


def require_role(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Этой роли действие недоступно")
        return user

    return dependency


def _bundle() -> dict:
    bundle = load_workspace()
    if bundle is None:
        raise HTTPException(status_code=404, detail="Расчёт ещё не выполнен. Загрузите выгрузку 1С на сайте.")
    return bundle


def _order_view(state: dict) -> dict:
    return {key: value for key, value in state.items() if key != "asOf"}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": MODEL_NAME, "ready": MODEL_PATH.exists()}


@app.post("/v1/auth/login")
def login(body: LoginIn) -> dict:
    user = authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return {"token": issue_token(user), **public_user(user)}


@app.get("/v1/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@app.get("/v1/bundle")
def bundle(_: dict = Depends(current_user)) -> dict:
    """Same JSON the mobile Bundle.fromJson already reads (kpis, lines, alerts, anomalies, series)."""
    return _bundle()


@app.get("/v1/orders/current")
def current_order(_: dict = Depends(current_user)) -> dict:
    return _order_view(get_order(_bundle()))


@app.post("/v1/orders/{order_id}/submit")
def submit_order(order_id: str, user: dict = Depends(require_role("buyer"))) -> dict:
    if order_id != ORDER_ID:
        raise HTTPException(status_code=404, detail="Неизвестный заказ")
    try:
        state = submit(user["name"], _bundle())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _order_view(state)


@app.post("/v1/orders/{order_id}/approve")
def approve_order(order_id: str, user: dict = Depends(require_role("director"))) -> dict:
    if order_id != ORDER_ID:
        raise HTTPException(status_code=404, detail="Неизвестный заказ")
    try:
        state = approve(user["name"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _order_view(state)


@app.post("/v1/orders/{order_id}/return")
def return_for_rework(order_id: str, body: CommentIn, user: dict = Depends(require_role("director"))) -> dict:
    if order_id != ORDER_ID:
        raise HTTPException(status_code=404, detail="Неизвестный заказ")
    try:
        state = return_order(user["name"], body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _order_view(state)


@app.post("/v1/sku/{code}/ask")
def ask_sku(code: str, body: AskIn, _: dict = Depends(current_user)) -> dict:
    data = _bundle()
    line = find_line(data, code)
    if line is None:
        raise HTTPException(status_code=404, detail="Артикул не найден в текущем заказе")
    return {"code": line.get("code"), "answer": answer(data, line, body.question)}


@app.get("/v1/sku/{code}/series")
def sku_series(code: str, _: dict = Depends(current_user)) -> dict:
    """Monthly points for the mini chart. Empty until the engine stores per-SKU history."""
    data = _bundle()
    line = find_line(data, code)
    if line is None:
        raise HTTPException(status_code=404, detail="Артикул не найден в текущем заказе")
    return {"code": line.get("code"), "points": []}


@app.post("/v1/workspace")
async def workspace(files: list[UploadFile] = File(...), supplier: str = "IEK") -> dict:
    uploads = [f for f in files if f.filename]
    if not uploads:
        raise HTTPException(status_code=400, detail="Загрузите выгрузки 1С (xlsx)")
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for upload in uploads:
            name = Path(upload.filename or "upload.xlsx").name
            (folder / name).write_bytes(await upload.read())
        try:
            built = build_workspace(folder, supplier)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    from qor.orders import WORKSPACE_PATH

    WORKSPACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_PATH.write_text(json.dumps(built, ensure_ascii=False), encoding="utf-8")
    return built
