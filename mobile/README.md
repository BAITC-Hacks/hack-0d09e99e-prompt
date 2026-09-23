# Qor Mobile — согласование на ходу

Flutter-клиент для руководителя: риски, уведомления, утверждение / возврат заказа, «Спросить почему».
Таблиц, правки qty и экспорта в 1С здесь нет — это сайт.

## Запуск

```bash
cd mobile
flutter pub get
flutter run          # нужен iOS Simulator (sudo xcodebuild -license) или Android-эмулятор
flutter test         # расчётные тексты + прогон всех экранов на размере iPhone
```

## Данные

Пока API нет, `MockQorRepository` читает `assets/data/iek.json` — копию `../app/data/iek.json`
(тот же бандл, что у веба). Обновлять копией после `scripts/build_iek_bundle.py`.

Когда бэк будет готов — реализовать `QorRepository` (`lib/data/repository.dart`) через HTTP
и подменить `repositoryProvider` в `lib/data/providers.dart`. Экраны не трогаются.

Что мобилка ждёт от API:

| Метод | Зачем |
|---|---|
| бандл: `kpis`, `lines`, `alerts`, `anomalies`, `series` | всё, что сейчас в `iek.json` |
| статус заказа `pending_approval / approved / returned` + автор, время, комментарий | шапка заказа, главная, бейджи |
| `approve(orderId)` | кнопка «Утвердить» |
| `return(orderId, comment)` | «Вернуть на доработку» |
| `ask(sku, question)` → текст | чат «Спросить почему» (LLM) |
| помесячный ряд продаж по SKU (желательно) | мини-график; сейчас это оценка по сезонности IEK |

## Структура

```
lib/
  theme/     токены (как в tailwind.config.ts) и тема Material 3
  data/      модели, мок-репозиторий, провайдеры riverpod, тексты обоснований
  widgets/   бейджи срочности, карточка позиции, мини-график
  screens/   главная, заказ, карточка SKU, чат, уведомления, пуш-макет, профиль
```
