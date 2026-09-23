# Промт для Stitch AI — Web (рабочее место закупа)

Режим **Web**. Референсы: `docs/04-design-references.md` (только web-шоты).
Это **десктопный инструмент**, не адаптив мобилки. Плотность данных как Linear / Stripe Dashboard.

```text
Design a dense desktop B2B workspace (1440px, NOT a mobile-adaptive dashboard) called
"StockPilot" for a purchasing manager at electrical wholesaler ekt.kz (Almaty warehouse,
supplier IEK). This is the manager's daily workstation: big tables, inline qty edits,
calculation waterfall, anomaly review, LLM chat, export to 1C. Do NOT design a phone
layout, bottom tabs, swipe-to-approve, or a "mobile home" KPI grid.

Product: StockPilot Web. ALL LABELS IN RUSSIAN.

VISUAL SYSTEM (must match the mobile app tokens, but desktop density):
- Light theme, page bg #F5F7FA, cards #FFFFFF, accent #2563EB, Inter
- Radius 12, thin 1px borders #E5E7EB, tight 8/12/16 spacing
- Urgency badges (same component everywhere):
  Критично = #DC2626 on #FEF2F2
  Скоро = #D97706 on #FFFBEB
  Норма = #059669 on #ECFDF5
  Аномалия = #EA580C on #FFF7ED
- Monospace for SKU codes like MVA20-1-016-C, 200400085_

LEFT SIDEBAR (always):
Логотип StockPilot
Дашборд трендов
Заказы поставщикам  ← default
Аномалии
Согласование
Настройки расчёта
Footer: роль «Менеджер закупа · Алматы»

============================================================
SCREEN 1 — ЗАКАЗЫ ПОСТАВЩИКАМ  (CORE DEMO, design first)
============================================================
Top bar:
- Title «Заказы поставщикам»
- Filters: Склад [Алматы], Поставщик [IEK], Категория [Все]
- Secondary: «Горизонт: 8 недель»
- PRIMARY button «Пересчитать» (blue, with last-run time «22.09.2026 16:04»)

After calculation, a SUPPLIER GROUP header card:
  IEK  ·  847 позиций  ·  сумма ₸ 18.4 млн  ·  12 критично  ·  300 в пути
  Buttons: «Отправить на согласование» (primary), export disabled until approved
  Status chip: «Черновик» (later states: На согласовании / Утверждено / На доработке)

DENSE DATA TABLE (this is the hero, must look like a real 1C-adjacent grid):
Columns: ☐ | Артикул | Наименование | Ед. | Остаток | В пути (ETA) | Спрос/мес |
Прогноз 8 нед | Рек. кол-во (EDITABLE number input) | MOQ | Срочность | Δ правки
Sticky header, zebra optional, row height ~40px, 12–14 visible rows.

Real example rows (use these, not generic "Кабель"):
- MVA20-1-016-C  Автомат ВА47-29 1п 16А IEK    шт  4    120 (до 01.10)  86   172   48   MOQ 12   Скоро
- CS3-1C5EU      Разъём RJ-45 UTP кат.5Е ITK   шт  0    3000 (до 30.09) 410  820    0   MOQ 100  Норма
- 200400085_     F/UTP кат.5Е 305м ITK         м   9084 0              1800 3600   0   MOQ 305  Норма
- LDPA0-5030-1H-K01 Светильник авар. ДПА 5030  шт  0    0              22   44    60   MOQ 1    Критично

Clicking a row opens SCREEN 3 in a right split (or full page). Edited qty gets a
small blue delta «было 48 → 60» and does NOT auto-send anywhere.

Empty state before first run: illustration + «Запустите расчёт по складу Алматы».

============================================================
SCREEN 2 — АНОМАЛИИ
============================================================
Title «Исключённые разовые заказы»
Subtitle: «Эти накладные не вошли в регулярную потребность. Источник: динамика продаж.»
Table: Дата | № накладной | Артикул | Наименование | Кол-во | vs медиана SKU | Почему исключено
Example:
22.03.2026 | 20000099102 | MVA20-1-016-C | ВА47-29 16А | 1 200 шт | медиана 12 | IQR, разовая отгрузка
Toggle on a row: «Вернуть в расчёт» (dangerous, needs confirm). Orange anomaly badges.
No mobile cards — this is a forensic table.

============================================================
SCREEN 3 — КАРТОЧКА АРТИКУЛА  (CORE DEMO)
============================================================
Header: MVA20-1-016-C · Автомат ВА47-29 1п 16А IEK
Meta chips: поставщик IEK · ед. шт · MOQ 12 · срок поставки ~14 дн · склад Алматы
Stat row: Остаток 4 | В пути 120 до 01.10 (ПП УТ-7848) | Спрос 86/мес | Рек. 48

LEFT 60%:
- Chart 24 months (янв 2024–сен 2026): solid actuals, dashed forecast, red hatch =
  months with empty leftover (stockout), orange dots = excluded invoices.
- WATERFALL (must-have visual): horizontal bars
  База 86 → × сезонность 1.22 (июль) = 105 → + тренд +8 → + stockout +18
  → − аномалия −40 (накладная 20000099102) → − в пути −120 → ceil MOQ 12 → 48
  Each bar labeled. This is the "why this number" moment for the jury.

RIGHT 40%:
- LLM justification (3–4 sentences, Russian, citing the waterfall steps)
- Chat: input «Спросить модель…» + 2 suggested chips:
  «Почему не 0, если 120 уже в пути?»
  «Что будет, если не заказать до октября?»
- Thread bubbles. LLM answers with numbers from the engine, not fluff.

============================================================
SCREEN 4 — СОГЛАСОВАНИЕ + ЭКСПОРТ
============================================================
Order IEK in status «На согласовании» since 16:12, approver = руководитель.
Timeline: Черновик → Отправлен Айгерим → ждёт Данияра.
When status = Утверждено: primary «Экспорт в Excel (1С)» and «Экспорт CSV».
When status = На доработке: red comment from mobile «Снимите 16А, на складе Астаны есть остаток»
  + button «Открыть таблицу и поправить».
Export is DISABLED on Черновик and На согласовании. Never a "send to supplier" button.

============================================================
SCREEN 5 — ДАШБОРД ТРЕНДОВ (optional, last)
============================================================
Category demand 12 months: Автоматика, Кабель/ITK, Свет, Щитовое.
KPI: 797 SKU с пустым остатком в сент. 2026 · точность 87% · излишки ₸…
This screen is secondary. Do not make it the first artboard.

DO NOT include: bottom navigation, hamburger-only nav, swipe actions,
approval buttons as the primary CTA (manager SENDS to approval, boss approves on phone).
```
