# Qor — закупки ekt.kz

**Qor** (қаз. *қор* — запас). Рабочее место менеджера по закупкам: загрузите выгрузку 1С — получите заказы поставщикам.

Каталог в продукт не вшит. Веб только показывает расчёт после загрузки Excel. Модель спроса обучается отдельно.

## Папки

- `frontend/` — Next.js, экраны закупщика.
- `backend/` — движок расчёта (`build_iek_bundle.py`). Фронт вызывает его при загрузке файлов.
- `docs/` — постановка и схема выгрузок.

## Запуск

```bash
cd frontend
npm install
npm run dev
```

Открыть [http://localhost:3000](http://localhost:3000).

Зависимости движка: `pip install -r backend/requirements.txt`.

Экраны: `/` дашборд, `/import` выгрузка, `/orders` заказы, `/sku/[артикул]` карточка, `/anomalies`, `/suppliers`.

Результат расчёта лежит в `backend/data/workspace.json` и в git не попадает.

Локальная папка для кнопки «демо»: `/Users/azamatomirtaj/Documents/IEK`. Схема файлов — `docs/06-datasets.md`.
