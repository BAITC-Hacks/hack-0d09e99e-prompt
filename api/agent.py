"""Данные для AI-ассистента.

Источник — тот же файл, который рисуют сайт и телефон
(backend/data/workspace.json). Раньше агент читал отдельный снимок
data/processed/recommended_orders_v2.json, и числа в чате расходились
с таблицей: снимок не пересчитывался при загрузке новой выгрузки.
"""

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

WORKSPACE_FILE = Path(
    os.environ.get(
        "QOR_OUT",
        ROOT / "backend" / "data" / "workspace.json",
    )
)

# Как срочность называется в расчёте и как о ней говорит ассистент.
URGENCY_RU = {
    "critical": "критично",
    "warning": "скоро",
    "safe": "норма",
}


def load_workspace() -> dict:
    if not WORKSPACE_FILE.exists():
        raise FileNotFoundError(
            "Расчёт ещё не выполнен: нет "
            f"{WORKSPACE_FILE.name}. "
            "Загрузите выгрузку 1С на сайте."
        )
    with open(WORKSPACE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _safety_stock(line: dict) -> float:
    """Страховой запас лежит шагом водопада, отдельного поля нет."""
    for step in line.get("steps") or []:
        if step.get("key") == "season":
            return float(step.get("delta") or 0)
    return 0.0


def _reason(line: dict) -> str:
    """Причина одной строкой — из тех же чисел, что видит закупщик."""
    parts = []
    if line.get("stockoutNow"):
        parts.append("на складе пусто")
    else:
        parts.append(f"остаток {line.get('stock')}")
    if float(line.get("inTransit") or 0) > 0:
        parts.append(f"в пути {line.get('inTransit')}")
    parts.append(f"прогноз {line.get('demandMonth')}/мес")
    if line.get("forecastSource") != "model":
        parts.append("прогноз по месяцам с наличием: модель занижена из-за дефицита")
    if int(line.get("moq") or 1) > 1:
        parts.append(f"округлено до MOQ {line.get('moq')}")
    return ", ".join(parts)


def compact(line: dict, supplier: str) -> dict:
    """Плоская проекция для ответа модели: только то, что нужно человеку."""
    return {
        "name": (line.get("name") or "").strip(),
        "sku": line.get("code"),
        "article": line.get("article"),
        "supplier": supplier,
        "recommended": line.get("recommended"),
        "moq": line.get("moq"),
        "unit": line.get("unit"),
        "forecast": line.get("demandMonth"),
        "free_stock": line.get("stock"),
        "incoming": line.get("inTransit"),
        "safety_stock": _safety_stock(line),
        "urgency": URGENCY_RU.get(line.get("urgency"), line.get("urgency")),
        "stockout_now": line.get("stockoutNow"),
        "reason": _reason(line),
    }


def _trustworthy(line: dict) -> bool:
    """Тот же фильтр, что у витрины сайта (pipeline.trustworthy).

    Без него ассистент бодро советует позиции, которых сайт не показывает:
    без истории наличия рекомендация не обоснована.
    """
    return (
        not line.get("neverStocked")
        and not line.get("noStockRecord")
        and int(line.get("monthsUsed") or 0) >= 3
    )


def _lines(workspace: dict) -> list[dict]:
    return [line for line in (workspace.get("lines") or []) if _trustworthy(line)]


def get_critical_orders(limit: int = 10) -> list[dict]:
    workspace = load_workspace()
    supplier = workspace.get("supplier", "")
    critical = [
        compact(line, supplier)
        for line in _lines(workspace)
        if line.get("urgency") in ("critical", "warning")
        and int(line.get("recommended") or 0) > 0
    ]
    return critical[:limit]


def get_supplier_orders(supplier: str, limit: int = 20) -> list[dict]:
    workspace = load_workspace()
    current = workspace.get("supplier", "")
    if supplier.strip().lower() != current.strip().lower():
        return {
            "error": (
                f"В текущем расчёте только поставщик {current}. "
                f"По «{supplier}» данных нет."
            )
        }
    return [
        compact(line, current)
        for line in _lines(workspace)
        if int(line.get("recommended") or 0) > 0
    ][:limit]


def get_order_by_sku(sku: str) -> dict:
    workspace = load_workspace()
    needle = sku.strip().lower()
    for line in _lines(workspace):
        if (
            str(line.get("code", "")).lower() == needle
            or str(line.get("article", "")).lower() == needle
        ):
            return compact(line, workspace.get("supplier", ""))
    return {"error": f"SKU {sku} не найден в текущем заказе"}


def simulate_order(sku: str, quantity: int) -> dict:
    order = get_order_by_sku(sku)
    if "error" in order:
        return order

    forecast = float(order["forecast"] or 0)
    free_stock = float(order["free_stock"] or 0)
    incoming = float(order["incoming"] or 0)
    safety_stock = float(order["safety_stock"] or 0)

    total_available = free_stock + incoming + quantity
    projected_stock = total_available - forecast
    shortage = max(forecast + safety_stock - total_available, 0)

    if shortage > 0:
        risk = "высокий"
    elif projected_stock < safety_stock:
        risk = "средний"
    else:
        risk = "низкий"

    return {
        "sku": sku,
        "name": order["name"],
        "simulated_order": quantity,
        "recommended": order["recommended"],
        "forecast": forecast,
        "free_stock": free_stock,
        "incoming": incoming,
        "safety_stock": safety_stock,
        "projected_stock": round(projected_stock, 2),
        "shortage": round(shortage, 2),
        "risk": risk,
    }
