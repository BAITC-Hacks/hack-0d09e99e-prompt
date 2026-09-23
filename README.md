# Qor — закупки ekt.kz

**Qor** (қаз. *қор* — запас). Рабочее место менеджера по закупкам: расчёт заказов IEK по выгрузке 1С.

## Запуск веба

```bash
npm install
npm run dev
```

Открыть [http://localhost:3000](http://localhost:3000).

Экраны: `/` дашборд, `/orders` заказы, `/sku/[артикул]` карточка, `/anomalies`, `/suppliers`.

Данные: `app/data/iek.json` собирается скриптом `python3 scripts/build_iek_bundle.py` из `/Documents/IEK`.

## Данные

Реальные выгрузки IEK: `/Users/azamatomirtaj/Documents/IEK`. Схема — `docs/06-datasets.md`.
