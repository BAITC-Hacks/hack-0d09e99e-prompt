import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI, OpenAIError

from api.agent import (
    get_critical_orders,
    get_supplier_orders,
    get_order_by_sku,
    simulate_order,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY не найден. "
        "Добавь его в .env"
    )


# ============================================================
# OPENAI
# ============================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)

MODEL = "gpt-5.6"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="QOR AI Procurement Agent",
    description=(
        "AI-ассистент для анализа спроса "
        "и формирования рекомендаций закупки."
    ),
    version="1.0.0",
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class SimulationRequest(BaseModel):
    sku: str
    quantity: int


# ============================================================
# OPENAI TOOLS
# ============================================================

TOOLS = [
    # --------------------------------------------------------
    # CRITICAL ORDERS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_critical_orders",
            "description": (
                "Получить наиболее критичные позиции, "
                "которые рекомендуется заказать. "
                "Используй этот инструмент, если пользователь "
                "спрашивает, что срочно или критично заказать."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Максимальное количество позиций."
                        ),
                        "default": 10,
                    }
                },
            },
        },
    },

    # --------------------------------------------------------
    # SUPPLIER ORDERS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_supplier_orders",
            "description": (
                "Получить рекомендации закупки "
                "по конкретному поставщику. "
                "Поддерживаются IEK и Systeme."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier": {
                        "type": "string",
                        "description": (
                            "Название поставщика: "
                            "IEK или Systeme."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Количество позиций."
                        ),
                        "default": 20,
                    },
                },
                "required": [
                    "supplier"
                ],
            },
        },
    },

    # --------------------------------------------------------
    # SKU
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_order_by_sku",
            "description": (
                "Получить полную информацию по конкретному SKU: "
                "прогноз спроса, остаток, товар в пути, MOQ, "
                "рекомендуемый заказ, риск и сигналы модели."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": (
                            "Код SKU, например 130300792_."
                        ),
                    }
                },
                "required": [
                    "sku"
                ],
            },
        },
    },

    # --------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "simulate_order",
            "description": (
                "Смоделировать заказ другого количества товара. "
                "Используй, если пользователь спрашивает, "
                "что произойдет, если заказать определенное "
                "количество единиц SKU."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": (
                            "Код SKU."
                        ),
                    },
                    "quantity": {
                        "type": "integer",
                        "description": (
                            "Количество единиц для симуляции."
                        ),
                    },
                },
                "required": [
                    "sku",
                    "quantity",
                ],
            },
        },
    },
]


# ============================================================
# TOOL EXECUTOR
# ============================================================

def execute_tool(
    name: str,
    arguments: dict,
):
    """
    Выполняет локальные функции QOR.

    OpenAI не рассчитывает прогнозы самостоятельно.
    Все числовые значения приходят из Procurement Engine.
    """

    if name == "get_critical_orders":
        return get_critical_orders(
            arguments.get(
                "limit",
                10,
            )
        )

    if name == "get_supplier_orders":
        return get_supplier_orders(
            arguments["supplier"],
            arguments.get(
                "limit",
                20,
            ),
        )

    if name == "get_order_by_sku":
        return get_order_by_sku(
            arguments["sku"]
        )

    if name == "simulate_order":
        return simulate_order(
            arguments["sku"],
            arguments["quantity"],
        )

    return {
        "error": (
            f"Неизвестный инструмент: {name}"
        )
    }


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
Ты QOR — AI-ассистент отдела закупок.

Твоя задача — помогать менеджеру анализировать прогноз спроса,
остатки, товар в пути и рекомендации закупки.

ВАЖНЫЕ ПРАВИЛА:

1. Никогда не придумывай числовые значения.

2. Для информации о SKU, прогнозах, остатках,
товарах в пути, MOQ и рекомендуемых заказах
используй предоставленные инструменты.

3. Рекомендуемое количество заказа рассчитывает
Procurement Engine QOR, а не языковая модель.

4. Если пользователь спрашивает:
"Что нужно заказать?"
используй get_critical_orders.

5. Если пользователь спрашивает про IEK или Systeme,
используй get_supplier_orders.

6. Если пользователь указывает конкретный SKU,
используй get_order_by_sku.

7. Если пользователь спрашивает:
"Что будет, если заказать X штук?",
используй simulate_order.

8. Объясняй результат понятным языком.

9. Для рекомендации желательно указывать:
- SKU;
- прогноз спроса;
- свободный остаток;
- товар в пути;
- рекомендуемый заказ;
- риск;
- срочность.

10. Если risk HIGH или urgency CRITICAL,
обязательно предупреди о риске дефицита.

11. Не утверждай, что заказ уже отправлен поставщику.
QOR только формирует рекомендацию.

12. Отвечай на русском языке,
если пользователь не попросил другой язык.
"""


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "QOR AI",
        "model": MODEL,
    }


# ============================================================
# DIRECT PROCUREMENT ENDPOINTS
# ============================================================

@app.get("/orders/critical")
def critical_orders(
    limit: int = 10,
):
    return get_critical_orders(
        limit
    )


@app.get("/orders/supplier/{supplier}")
def supplier_orders(
    supplier: str,
    limit: int = 20,
):
    return get_supplier_orders(
        supplier,
        limit,
    )


@app.get("/orders/sku/{sku}")
def order_by_sku(
    sku: str,
):
    return get_order_by_sku(
        sku
    )


@app.post("/orders/simulate")
def simulate(
    request: SimulationRequest,
):
    return simulate_order(
        request.sku,
        request.quantity,
    )


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):
    """
    QOR AI chat.

    Шаги:

    User
      ↓
    GPT-5.6
      ↓
    Tool selection
      ↓
    Procurement Engine
      ↓
    GPT-5.6
      ↓
    Human-readable answer
    """

    try:
        # ----------------------------------------------------
        # INITIAL MESSAGES
        # ----------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": request.message,
            },
        ]

        # ----------------------------------------------------
        # FIRST OPENAI REQUEST
        #
        # reasoning_effort="none" важен для function tools
        # через Chat Completions с GPT-5.6.
        # ----------------------------------------------------

        response = (
            client.chat.completions.create(
                model=MODEL,

                messages=messages,

                tools=TOOLS,

                tool_choice="auto",

                reasoning_effort="none",
            )
        )

        assistant_message = (
            response
            .choices[0]
            .message
        )

        # ----------------------------------------------------
        # MODEL DID NOT NEED A TOOL
        # ----------------------------------------------------

        if not assistant_message.tool_calls:
            return {
                "answer":
                    assistant_message.content,

                "tools_used": [],
            }

        # ----------------------------------------------------
        # ADD ASSISTANT TOOL REQUEST
        # ----------------------------------------------------

        messages.append(
            assistant_message
        )

        tools_used = []

        # ----------------------------------------------------
        # EXECUTE TOOL CALLS
        # ----------------------------------------------------

        for tool_call in (
            assistant_message.tool_calls
        ):
            tool_name = (
                tool_call
                .function
                .name
            )

            tools_used.append(
                tool_name
            )

            try:
                arguments = json.loads(
                    tool_call
                    .function
                    .arguments
                )

            except json.JSONDecodeError:
                arguments = {}

            print(
                f"QOR tool call: "
                f"{tool_name} "
                f"{arguments}",
                flush=True,
            )

            tool_result = execute_tool(
                tool_name,
                arguments,
            )

            # -----------------------------------------------
            # TOOL RESPONSE
            # -----------------------------------------------

            messages.append(
                {
                    "role": "tool",

                    "tool_call_id":
                        tool_call.id,

                    "content":
                        json.dumps(
                            tool_result,
                            ensure_ascii=False,
                        ),
                }
            )

        # ----------------------------------------------------
        # FINAL OPENAI RESPONSE
        # ----------------------------------------------------

        final_response = (
            client.chat.completions.create(
                model=MODEL,

                messages=messages,

                tools=TOOLS,

                tool_choice="auto",

                reasoning_effort="none",
            )
        )

        final_message = (
            final_response
            .choices[0]
            .message
        )

        # ----------------------------------------------------
        # SAFETY FALLBACK
        # ----------------------------------------------------

        # Обычно после получения tool results
        # модель уже возвращает текст.
        #
        # Если вдруг она снова решила вызвать tool,
        # не создаём бесконечный цикл.

        if final_message.tool_calls:
            return {
                "answer": (
                    "QOR получил данные, но модель "
                    "запросила дополнительный расчёт. "
                    "Повторите вопрос более конкретно."
                ),

                "tools_used":
                    tools_used,
            }

        return {
            "answer":
                final_message.content,

            "tools_used":
                tools_used,
        }

    # ========================================================
    # OPENAI ERROR
    # ========================================================

    except OpenAIError as error:
        print(
            f"OpenAI error: {error}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Ошибка OpenAI API: "
                f"{str(error)}"
            ),
        )

    # ========================================================
    # INTERNAL ERROR
    # ========================================================

    except Exception as error:
        print(
            f"QOR internal error: {error}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Ошибка QOR: "
                f"{str(error)}"
            ),
        )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name":
            "QOR AI Procurement Agent",

        "status":
            "running",

        "docs":
            "/docs",

        "endpoints": [
            "/chat",
            "/health",
            "/orders/critical",
            "/orders/supplier/{supplier}",
            "/orders/sku/{sku}",
            "/orders/simulate",
        ],
    }