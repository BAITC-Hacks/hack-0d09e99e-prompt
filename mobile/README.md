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

## API

База: `http://127.0.0.1:8000`. Swagger: `/docs`. Все методы кроме `/health` и `/v1/auth/login` требуют `Authorization: Bearer <token>`.

Демо-логины (пароли переопределяются `QOR_BUYER_PASSWORD` / `QOR_DIRECTOR_PASSWORD`):

| Логин | Пароль | Роль | Кто |
|---|---|---|---|
| `aigerim` | `buyer` | `buyer` | менеджер закупа, отправляет на согласование |
| `daniyar` | `director` | `director` | руководитель, утверждает или возвращает |

`id` текущего заказа всегда `iek-current`. Статусы: `draft` → `pending_approval` → `approved` | `returned`. Утверждение не отправляет заказ поставщику.

| Метод | Кто | Тело | Ответ |
|---|---|---|---|
| `POST /v1/auth/login` | все | `{ "username", "password" }` | `{ token, username, role, name, title }` |
| `GET /v1/me` | все | | профиль |
| `GET /v1/bundle` | все | | тот же JSON, что `Bundle.fromJson` (`kpis`, `lines`, `alerts`, `anomalies`, `series`, `seasonOct`) |
| `GET /v1/orders/current` | все | | `{ id, status, sentBy, sentAt, decidedBy, decidedAt, comment }` |
| `POST /v1/orders/iek-current/submit` | buyer | | статус `pending_approval` |
| `POST /v1/orders/iek-current/approve` | director | | статус `approved` |
| `POST /v1/orders/iek-current/return` | director | `{ "comment" }` | статус `returned` |
| `POST /v1/sku/{code}/ask` | все | `{ "question" }` | `{ code, answer }` |
| `GET /v1/sku/{code}/series` | все | | `{ code, points }` — пока пустой ряд, мини-график остаётся на оценке |

404 на бандле значит, что расчёт ещё не записан в `backend/data/workspace.json` (загрузка на сайте). Пока файла нет, `MockQorRepository` по-прежнему читает `assets/data/iek.json`.

HTTP-клиент: реализовать `QorRepository` (`lib/data/repository.dart`) и подменить `repositoryProvider` в `lib/data/providers.dart`. Экраны не трогаются. `approve` / `return` с чужой роли отвечают 403, повторное утверждение — 409.

## Структура

```
lib/
  theme/     токены (как в tailwind.config.ts) и тема Material 3
  data/      модели, мок-репозиторий, провайдеры riverpod, тексты обоснований
  widgets/   бейджи срочности, карточка позиции, мини-график
  screens/   главная, заказ, карточка SKU, чат, уведомления, пуш-макет, профиль
```
