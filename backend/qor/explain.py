"""Short answers for the mobile «Спросить почему» chat.

Built only from numbers already on the order line. No client identifiers.
"""

from __future__ import annotations


def _qty(value: float) -> str:
    number = float(value)
    if abs(number - round(number)) < 1e-9 or abs(number) >= 100:
        return f"{round(number):,}".replace(",", " ")
    return f"{number:.1f}".replace(".", ",")


def _anomaly_for(bundle: dict, code: str) -> dict | None:
    best = None
    for item in bundle.get("anomalies") or []:
        if item.get("code") != code and item.get("article") != code:
            continue
        if best is None or float(item.get("qty") or 0) > float(best.get("qty") or 0):
            best = item
    return best


def find_line(bundle: dict, code: str) -> dict | None:
    needle = code.strip()
    for item in bundle.get("lines") or []:
        if item.get("code") == needle or item.get("article") == needle:
            return item
    for item in bundle.get("alerts") or []:
        if item.get("code") == needle or item.get("article") == needle:
            return item
    return None


def answer(bundle: dict, line: dict, question: str) -> str:
    unit = line.get("unit") or "шт"
    season = float(bundle.get("seasonOct") or 1)
    horizon = int(bundle.get("horizonWeeks") or 4)
    demand = float(line.get("demandMonth") or 0)
    lost = float(line.get("lostDemand") or 0)
    stock = float(line.get("stock") or 0)
    transit = float(line.get("inTransit") or 0)
    recommended = float(line.get("recommended") or 0)
    moq = float(line.get("moq") or 1)
    days = int(line.get("daysLeft") or 0)
    eta = line.get("inTransitEta") or "срок в выгрузке не указан"
    anomaly = _anomaly_for(bundle, str(line.get("code") or ""))
    q = question.lower()

    if "пути" in q:
        if transit > 0:
            return (
                f"Да: {_qty(transit)} {unit}, {eta}. "
                f"Это уже вычтено из рекомендации {_qty(recommended)} {unit}."
            )
        return (
            f"Нет, в пути по этому артикулу ничего нет. "
            f"Заказ считается от остатка {_qty(stock)} {unit}."
        )

    if "утверд" in q or "как есть" in q:
        return (
            "Заказ получит статус «Утверждено», менеджер выгрузит его в 1С. "
            "Поставщику автоматически ничего не уходит. "
            f"По этой позиции {_qty(recommended)} {unit} закроют около {horizon} недель спроса."
        )

    if "не заказ" in q or "если не" in q:
        when = "уже сейчас" if line.get("stockoutNow") else f"через {days} дн."
        week = float(line.get("demandWeek") or 0)
        return (
            f"Остаток закончится {when}, а новая поставка идёт около 14 дн. "
            f"Упущенный спрос — около {_qty(week)} {unit} в неделю."
        )

    parts = [f"Спрос {_qty(demand)} {unit}/мес × сезон {season:.2f}".replace(".", ",")]
    if lost > 0:
        parts.append(f"+ {_qty(lost)} упущенного спроса")
    parts.append(f"− остаток {_qty(stock)}")
    if transit > 0:
        parts.append(f"− в пути {_qty(transit)}")
    text = " ".join(parts) + f" → {_qty(recommended)} {unit}."
    if moq > 1:
        text += f" Округлено до кратности MOQ {_qty(moq)}."
    if anomaly:
        text += (
            f" Накладная {anomaly.get('invoice')} на {_qty(float(anomaly.get('qty') or 0))} {unit} "
            "в регулярный спрос не вошла."
        )
    elif line.get("stockoutNow"):
        text += " Сейчас остатка нет — без заказа продажи будут упущены."
    return text
