import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

ORDERS_FILE = (
    ROOT
    / "data"
    / "processed"
    / "recommended_orders_v2.json"
)


def load_orders():
    if not ORDERS_FILE.exists():
        raise FileNotFoundError(
            "recommended_orders_v2.json не найден. "
            "Сначала запусти generate_orders_v2.py"
        )

    with open(
        ORDERS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_critical_orders(limit: int = 10):
    orders = load_orders()

    critical = [
        order
        for order in orders
        if order["order_required"]
        and order["risk"]["urgency"]
        in ["CRITICAL", "HIGH"]
    ]

    return critical[:limit]


def get_supplier_orders(
    supplier: str,
    limit: int = 20,
):
    orders = load_orders()

    supplier_lower = supplier.lower()

    result = [
        order
        for order in orders
        if order["supplier"].lower()
        == supplier_lower
        and order["order_required"]
    ]

    return result[:limit]


def get_order_by_sku(sku: str):
    orders = load_orders()

    for order in orders:
        if (
            order["sku"].lower()
            == sku.lower()
        ):
            return order

    return {
        "error": f"SKU {sku} не найден"
    }


def simulate_order(
    sku: str,
    quantity: int,
):
    order = get_order_by_sku(sku)

    if "error" in order:
        return order

    forecast = order["forecast"]

    free_stock = (
        order["inventory"]["free_stock"]
    )

    incoming = (
        order["inventory"]["incoming"]
    )

    safety_stock = (
        order["procurement"]["safety_stock"]
    )

    projected_stock = (
        free_stock
        + incoming
        + quantity
        - forecast
    )

    required_with_safety = (
        forecast
        + safety_stock
    )

    total_available = (
        free_stock
        + incoming
        + quantity
    )

    shortage = max(
        required_with_safety
        - total_available,
        0,
    )

    if shortage > 0:
        risk = "HIGH"
    elif projected_stock < safety_stock:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "sku": sku,
        "simulated_order": quantity,
        "forecast": forecast,
        "free_stock": free_stock,
        "incoming": incoming,
        "safety_stock": safety_stock,
        "projected_stock": round(
            projected_stock,
            2,
        ),
        "shortage": round(
            shortage,
            2,
        ),
        "risk": risk,
    }