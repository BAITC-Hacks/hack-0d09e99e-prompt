# Qor — закупки ekt.kz

**Qor** (қаз. *қор* — запас). Рабочее место менеджера по закупкам: загрузите выгрузку 1С — получите заказы поставщикам.

Каталог в продукт не вшит. Веб только показывает расчёт после загрузки Excel. Модель спроса обучается отдельно.

## Папки

- `frontend/` — Next.js, экраны закупщика.
- `backend/` — заказ по модели. `run_workspace.py` читает выгрузку 1С, считает признаки как при обучении и прогоняет `ml/models/demand_model.cbm`. API: `uvicorn main:app` из `backend/`.
- `docs/` — постановка и схема выгрузок.

## Запуск

```bash
cd frontend
npm install
npm run dev
```

Открыть [http://localhost:3000](http://localhost:3000).

Зависимости движка: `pip install -r backend/requirements.txt`.

Отдельный API (его же вызывает мобилка):

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Схема и демо-логины: `mobile/README.md`. Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Экраны: `/` дашборд, `/import` выгрузка, `/orders` заказы, `/sku/[артикул]` карточка, `/anomalies`, `/suppliers`.

Результат расчёта лежит в `backend/data/workspace.json` и в git не попадает.

Локальная папка для кнопки «демо»: `/Users/azamatomirtaj/Documents/IEK`. Схема файлов — `docs/06-datasets.md`.
