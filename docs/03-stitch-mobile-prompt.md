# Промт для Stitch AI — Mobile (согласование на ходу)

Режим **Mobile**. Референсы: `docs/04-design-references.md` (mobile / warehouse app).
Это **не** уменьшенный сайт. Нет таблиц, нет экспорта в 1С, нет запуска расчёта.
Пользователи: руководитель (утверждает) и менеджер вне офиса (смотрит риски).

Будет собрано на Flutter / Material 3. Дизайн можно в iOS-density, но крупные тач-зоны.

```text
Design a native mobile app (iPhone 14, 390px) called "StockPilot Approve" — an
approval-and-alerts companion. Users: a director who approves supplier orders on
the go, and a purchasing manager away from the desk.

THIS IS NOT A MINI DASHBOARD. Do NOT put:
- data tables, column grids, Excel export, "Пересчитать", calculation settings,
  waterfall with 7 steps, sidebar, category trend charts, inline qty editors.

Product: StockPilot. ALL LABELS IN RUSSIAN.
Same design tokens as the web workspace:
- bg #F5F7FA, cards #FFFFFF radius 16, accent #2563EB, Inter
- Urgency: Критично #DC2626/#FEF2F2 · Скоро #D97706/#FFFBEB · Норма #059669/#ECFDF5
- Large tap targets (min 48px). Bottom nav, not a hamburger.

============================================================
SCREEN 1 — ГЛАВНАЯ  (CORE)
============================================================
Role chip in header: «Руководитель · Данияр» (not the buyer).
Date: 23 сентября
Three BIG status cards only (not a 2x2 analytics grid):
1. «5 артикулов закончатся раньше поставки»  — Критично, tappable
2. «1 заказ ждёт вашего утверждения»         — accent blue, tappable → Screen 3
3. «IEK · ₸ 18.4 млн · 847 позиций»          — the pending order sum

Then a short "Сегодня" feed (3 items, not a dashboard):
- 13:04  MVA20-1-016-C остаток 4 шт, в пути 120 до 01.10
- 12:50  Заказ IEK отправлен на согласование Айгерим
- 09:10  797 SKU без остатка в сентябре (инфо, не паника)

NO charts on home. NO "точность прогноза 87%". This is a control tower, not analytics.

============================================================
SCREEN 2 — УВЕДОМЛЕНИЯ + PUSH MOCK
============================================================
A) In-app notification list:
- Критично: «MVA20-1-016-C закончится через 5 дней, срок поставки 14 дней»
  CTA: «Открыть артикул»
- Акцент: «Заказ поставщику IEK готов к утверждению · 847 позиций · ₸ 18.4 млн»
  CTA: «Рассмотреть»
- Инфо: «ПП УТ-7848 приедет 01.10 · 59 567 шт»

B) iOS PUSH MOCK (separate artboard, lock screen):
Title: StockPilot
Body: Заказ IEK на ₸ 18.4 млн ждёт утверждения
This artboard is for the jury demo photo. Design it.

============================================================
SCREEN 3 — ЗАКАЗ ПОСТАВЩИКА  (CORE DEMO)
============================================================
Header: «Заказ IEK»  status chip «На согласовании»
Meta: от Айгерим, 23.09 16:12, склад Алматы, 847 позиций
Urgency summary pills: 12 критично · 41 скоро · остальные норма

SCROLLABLE POSITION CARDS (not a table). Each card:
- SKU + short name
- urgency badge
- Остаток · В пути · Рек. 48 шт  (read-only, no +/− stepper)
- one-line why: «сезон 1.22 + stockout, накладная 1200 шт исключена»
Tap card → Screen 4.

STICKY BOTTOM BAR (the point of the app):
Итого ₸ 18.4 млн
[Вернуть на доработку] outline + [Утвердить] solid green/blue

«Вернуть» opens a comment sheet: textarea «Что исправить?» + send.
«Утвердить» opens confirm: «Заказ не уйдёт поставщику — только статус в системе
и экспорт в 1С на сайте. Подтвердить?»  Then success: «Утверждено. Айгерим
может выгрузить в 1С».

NO export button. NO qty edit. If the boss disagrees with a number, he returns
the whole order — the buyer fixes it on the website.

============================================================
SCREEN 4 — КАРТОЧКА АРТИКУЛА (LIGHT)
============================================================
MVA20-1-016-C
Автомат ВА47-29 1п 16А IEK
Mini chart (spark+area, 12 months only): actual line, dashed forecast,
one red band for stockout. NO waterfall here.

3 numbers: На складе 4 · В пути 120 · Рек. 48
LLM blurb, 2 sentences max:
«48 шт — это 8 недель спроса с летней сезонностью. Разовая накладная на 1 200 шт
в марте исключена, иначе заказ был бы втрое больше.»

Primary: «Спросить почему» → SCREEN 5
Secondary: «К заказу IEK»

============================================================
SCREEN 5 — СПРОСИТЬ ПОЧЕМУ (chat / voice)
============================================================
Chat with the same LLM as the website, but short answers.
Suggested chips:
- «Почему так много?»
- «Что если утвердить как есть?»
- «Есть ли уже товар в пути?»
Voice button on the input (waveform icon). Answers cite leftovers and ETA,
never invent a customer name (we have no client IDs in the dump).

============================================================
NAV
============================================================
Bottom: Главная · Заказы · Уведомления · Профиль
NO «Аналитика», NO «Настройки расчёта».

Optional extra artboard: returned-order state on this phone
(comment visible, Approve disabled) — nice for demo, not required.
```
