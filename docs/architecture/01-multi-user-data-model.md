# Этап 1 — Модель данных и подготовка к multi-user (≤10)

**Дата:** 2026-08-04
**Статус:** анализ, без правок кода
**Масштаб анализа:** 21 SQLAlchemy-модель, 21 репозиторий, migration_service.py (845 строк),
database.py, весь offline-слой фронта (IndexedDB, react-query persister, sync queue)

## 1. Ключевые факты (подтверждены в коде)

- **Multi-tenant отсутствует.** Grep по `user_id | owner_id | workspace_id | tenant | owner` — 0 совпадений.
  Ни одна из 21 модели не ссылается на `users`.
- **Auth отсутствует.** `UserModel`/`UserRepository`/`password_hash` — мёртвые скаффолды.
  Ни один роутер не использует `Depends(get_current_user)`. `password_hash="dummy"` только
  в dev-сиде `backend/seed.py:21`, в рантайме `users` не читается.
- **Alembic — мёртвая конфигурация.** 5 ревизий в `backend/migrations/versions/` не вызываются
  нигде в коде/CI. Реальные миграции — `app/services/migration_service.py` внутри `init_db()`
  (`app/database.py:59-91`) + одноразовые миграции по `PRAGMA user_version`
  (`_apply_onetime_migrations`, версии 1–9).
- **Offline-кэш не скоупнут по пользователю:** IndexedDB `bizibox-offline` v3 (сторы
  `mutations/messages/contacts/orders/tasks`, ключи по `id`), localStorage-persister
  `BIZIBOX_RQ_CACHE` (`App.tsx:47-50`), react-query кейки в `hooks/queries.ts` без user-префикса.
- **Экспорт (`app/routers/export.py`) глобальный и неполный** — 7 из 21 таблицы, без associations,
  каналов, настроек, шаблонов, сценариев, KB, import_mappings.
- **`channels.config`** хранит зашифрованные (Fernet, глобальный `ENCRYPTION_KEY`) учётные данные
  Telegram/email — самые чувствительные данные, обязаны быть per-owner в первую очередь.

## 2. Связи моделей, отсутствующие FK/индексы (Вопрос 1)

```
users  ← (никто не ссылается — изолирована)
contacts ─┬→ messages (contact_id NOT NULL)
          ├→ orders (contact_id NOT NULL)
          ├→ tasks (contact_id nullable)
          ├→ contact_fields, contact_notes (ondelete=CASCADE)
          ├→ suppliers.contact_id (nullable)
          └ m2m: contact_tags, categories, contact_type_templates
messages ─┬→ attachments (message_attachments)
          └ m2m categories
orders → order_items → products (через product_id)
products → categories, suppliers; → product_comments
categories → self parent_id; → products
```

Проблемы:
- `order_items.product_id` — FK есть, relationship `product` **не определён** (`order.py:33`).
- `tasks.message_id` — **вообще нет `ForeignKey`**, просто `Integer` (`task.py:29`).
- `orders.message_id` — FK есть, но без relationship.
- `suppliers.contact_id` — FK+relationship есть, но без обратной связи на contact.
- Избыточное индексирование низкокардинальных boolean-полей на `contacts`
  (`is_known, is_important, is_spam, chat_type, contact_type, life_sphere`) — при 10
  пользователях без owner_id эти индексы масштабируются линейно, а не логарифмически.

**Дрейф модели↔миграции (риск целостности, требует фикса до composite-unique):**
- `messages`: модель — безусловный `UniqueConstraint("channel","channel_message_id")`
  (`message.py:30`); миграция — частичный `WHERE deleted_at IS NULL`
  (`migration_service.create_indexes`). `create_all` на новой БД создаёт безусловный →
  возможны дубли строк с `deleted_at`.
- `contacts.telegram_id`: модель — `unique=True` безусловный (`contact.py:15`); миграция —
  частичный `WHERE telegram_id IS NOT NULL` (`uq_contacts_telegram_id`). Тот же конфликт.

## 3. Риски потери данных: nullable/дефолты (Вопрос 2)

- **`owner_id`** — главный риск при вводе: `NOT NULL` без backfill уронит `create_all`/ALTER
  на живой БД → добавлять nullable + backfill, НЕ NOT NULL на этом этапе.
- `messages.channel_message_id` nullable + безусловный unique в модели vs частичный в
  миграции → нужен dedup перед `(owner_id, channel, channel_message_id)`.
- `settings.value`/`scenarios.actions` JSON NOT NULL, `templates.content` NOT NULL,
  `import_mappings.mapping` TEXT NOT NULL — глобальные системные и per-owner записи
  сейчас смешаны в одних таблицах.

## 4. Вариант A vs B — рекомендация (Вопрос 3)

| Критерий | A — `owner_id` | B — таблица `workspace` |
|---|---|---|
| Сложность модели | 1 FK-колонка на таблицу | + таблица + FK + маппинг user↔workspace |
| Правка репозиториев | одинаково — нужен скоуп в каждом | + слой резолва workspace→user |
| Миграция данных | backfill `owner_id=1` | + seed workspace + маппинг |
| Offline-кэш | ключ по owner_id | ключ по workspace_id |
| Переезд на будущее | ренейм колонки | уже готов |

**Решение: Вариант A — `owner_id` (FK→`users.id`) на владельческих таблицах, без отдельной
таблицы `workspace`.** При ≤10 пользователях `user ≡ workspace 1:1`, отдельная таблица не даёт
выигрыша (YAGNI). Скоуп применяется на уровне репозиториев, не в виде DB-constraint (см. §7).

## 5. Миграция без потери данных (Вопрос 4)

Паттерн `_apply_onetime_migrations`, новые версии `PRAGMA user_version`:

1. **v10** — bootstrap owner: upsert пользователя `owner`/id=1 в `users`
   (`DEFAULT_OWNER_ID` в `config.py`); для всех владельческих таблиц:
   `ALTER TABLE <t> ADD COLUMN owner_id INTEGER` (nullable) →
   `UPDATE <t> SET owner_id = 1` → `CREATE INDEX idx_<t>_owner ON <t>(owner_id)`.
2. **v11** — фикс дрейфа: dedup `messages` по `(channel, channel_message_id)`,
   выравнивание частичных unique.
3. **v12** — composite-unique `(owner_id, col)` там, где сейчас глобальный unique.

Владельческие таблицы: `contacts, messages, orders, order_items, tasks, task_comments,
products, product_comments, suppliers, channels, contact_fields, contact_notes,
contact_tags, contact_folders, categories, contact_type_templates, templates, scenarios,
knowledge_base_examples, import_mappings, settings` + 4 association-таблицы.

Каждый шаг идемпотентен (существующий паттерн try/except + `PRAGMA user_version`).
Настоящего «нулевого даунтайма» не требуется — БД локальная, окно = перезапуск сервера.

## 6. Уникальность в рамках владельца (Вопрос 5)

- `users.username` — остаётся глобально уникальным (изолирована от owner-схемы).
- `contacts.telegram_id` → `unique(owner_id, telegram_id) WHERE telegram_id IS NOT NULL`.
- `messages.(channel, channel_message_id)` → `unique(owner_id, channel, channel_message_id)
  WHERE deleted_at IS NULL`.
- `products.sku`, `orders.order_number`, `categories.slug`, `contact_folders.category_key`,
  `contact_type_templates.slug` → composite `(owner_id, col)`.
- Дубли контактов (email/phone) — без жёсткого unique; дедуп через
  `ContactRepository.get_or_create`, перенастроенный на `(owner_id, telegram_id)` /
  `(owner_id, email)`.

## 7. Скоуп-механизм в коде (закреплено с пользователем)

**Через конструктор**, не per-call и не ContextVar:

```
роутер: Depends(get_current_user) → current_user.id
  → сервис: XService(session, owner_id=current_user.id)
    → репозиторий: BaseRepository(model, session, owner_id)
      → все CRUD-методы фильтруют .where(model.owner_id == self.owner_id)
```

**Причина отказа от per-call:** легко забыть аргумент → утечка данных между пользователями.
**Причина отказа от ContextVar:** фоновые async-задачи (PollService) теряют контекст.

**Критичный нюанс — фон вне HTTP-цепочки:** `PollService`, `channel_service.restore_channels()`
(`main.py:81`), AI-диспетчер работают без `current_user`. Скоуп для них определяет
**владелец сущности I/O** (`channels.owner_id`), а не пользователь сессии — резолвится в
`ChannelMessageService.process_incoming()` из владельца канала, не через ContextVar.

**Обязательный gating-тест:** все select() в наследниках репозиториев содержат фильтр owner_id;
негативный сценарий — запрос к строке чужого owner_id возвращает 404/пусто.

## 8. Auth — объём на этом этапе (закреплено с пользователем)

**Вариант A/C:** `owner_id`/миграция/offline-скоуп — сейчас. Полноценный login/JWT — релиз 2.

```python
async def get_current_user(session=Depends(get_session)):
    # РЕЛИЗ 1: вернуть бутстрапнутого дефолтного пользователя (DEFAULT_OWNER_ID)
    # РЕЛИЗ 2: распарсить JWT → вернуть реального пользователя
    return await UserRepository(session).get_by_id(DEFAULT_OWNER_ID)
```

Роутеры сразу пишут `current_user=Depends(get_current_user)` и пробрасывают `current_user.id`.
В релизе 2 меняется только тело функции — сервисы/репозитории не трогаются.
`init_db()` гарантирует существование дефолтного owner (v10, см. §5) — `users` перестаёт быть
мёртвой таблицей.

## 9. Системные/справочные таблицы (закреплено с пользователем — Вариант B)

`categories, contact_folders, contact_type_templates, templates, scenarios,
knowledge_base_examples, import_mappings` — справочные, не транзакционные.

**Решение: всё per-owner.** При создании owner сидятся **все** дефолты сразу (≤10 юзеров —
дублирование копеечное, offline-синхронизация остаётся однозначной, без «мой/не мой» в кеше).

Технические требования:
- Составной unique `(owner_id, slug)` вместо глобального `slug UNIQUE`.
- Новая колонка **`seed_version`** (Integer, default 0) в `categories, contact_folders,
  contact_type_templates` (при необходимости — `templates/scenarios`), чтобы новые релизные
  дефолты добавлялись без затирания отредактированных пользователем записей.
- `seed_default_categories/folders/contact_type_templates` переписываются на приём `owner_id`,
  `INSERT OR IGNORE` по `(owner_id, slug)`.

## 10. Offline-кэш при multi-user (Вопрос 6)

- **IndexedDB** `bizibox-offline` v3→v4: индекс `owner_id` в сторах
  `messages/contacts/orders/tasks`; `mutations` несёт `owner_id`.
- **localStorage-persister:** `BIZIBOX_RQ_CACHE` → `BIZIBOX_RQ_CACHE_<owner_id>`.
  `theme`/onboarding — остаются глобальными UI-предпочтениями.
- **react-query кейки** (`hooks/queries.ts`, 637 строк): user-префикс
  `['messages', ownerId, params]` и аналогично для всех остальных.
- `offline/merge.ts` (`incrementalFetch`, `mergeMessages`) и капы (`MAX_MESSAGES=500` и т.д.) —
  действуют в рамках owner_id.
- `offline/sync.ts` — очередь синка не смешивает мутации разных owner при переключении
  пользователя.

## 11. Быстрорастущие таблицы (Вопрос 7)

- **`messages`** растёт быстрее всех (фид каналов); капнута только в IndexedDB (500), в SQLite
  безлимитна; `extracted_entities`/`ai_draft_response` (JSON) раздувают строки.
- `order_items, contact_notes, task_comments, product_comments, message_attachments`
  (+ файлы на диске) — средний рост.
- `tasks, orders` — кап по открытым (status != done/archived).
- Пагинация (`skip/limit`, `min_id`) уже есть в базовом слое — распространить на все
  быстрорастущие списки + фоновая архивация messages старее N дней.

## 12. Денормализация/дублирование (Вопрос 8)

- `contacts.contact_type` + `category_override` (строки) **дублируют**
  `category_contact_association` (m2m) — `migration_service.migrate_contacts_to_categories`
  переносит одно в другое, создавая риск рассинхронизации.
- `messages.category` (строка) дублирует `category_message_association`.
- `contact_folders.category_key` дублирует `categories.scope='folder'`.
- Рекомендация: консолидировать на association-таблицах как единый источник истины —
  отдельный шаг вне владения (не блокирует ownership).

## 13. Мягкое vs физическое удаление (Вопрос 9)

- **Мягкое уже есть:** `contacts, messages, orders, tasks, suppliers` (`deleted_at`).
- **Добавить мягкое:** `products` (сейчас физическое), `categories, contact_tags,
  contact_folders, contact_type_templates` (на них ссылаются m2m/FS).
- **Физическое ок (каскадное):** `order_items, task_comments, product_comments,
  contact_notes, contact_fields, message_attachments` — потомки с
  `cascade="all, delete-orphan"`/`ondelete=CASCADE`.

## 14. Целостность message ↔ contact ↔ order ↔ task (Вопрос 10)

- message→contact ✓ (NOT NULL FK), order→contact ✓ (NOT NULL FK).
- order→message: FK есть, relationship нет — рабочее, но soft-delete message оставляет
  «висячую» ссылку в order (не критично, только soft).
- **task→message: FK отсутствует физически** (`task.py:29`) — риск при потенциальном
  жёстком удалении сообщений; рекомендация — добавить FK или гарантировать только
  soft-delete + owner-инвариант (оба id принадлежат одному owner_id).
- order_items.product_id: снапшот name/price уже денормализован верно — удаление продукта
  не рвёт историю заказа.

## 15. Экспорт/бэкап одного пользователя (Вопрос 11)

Текущий `export.py` — вся БД, 7 из 21 таблицы, без associations/каналов/настроек/шаблонов.
Для multi-user: фильтр по `owner_id` на каждой коллекции, покрыть все таблицы + associations,
`meta.owner_id` + версия схемы. `channels.config` (учётные данные Telegram/email) — отдельный
зашифрованный бэкап или исключение из обычного экспорта.

## 16. Безопасные изменения схемы (Вопрос 12)

- **Безопасно:** `ADD COLUMN owner_id NULL`, новые индексы, partial unique для новых строк,
  новые таблицы.
- **Средний риск:** backfill `UPDATE...SET owner_id=1` (идемпотентен, но нельзя мешать с
  новыми NULL-строками в процессе), NOT NULL — требует пересоздания таблицы (не в этом этапе).
- **Высокий риск:** смена глобальных unique → composite `(owner_id, col)` — нужен dedup
  сначала; консолидация `contact_type/category_override` → association (§12).

## 17. Итоговая дорожная карта

1. `feat-multi-user-schema` — owner_id везде + миграции v10-v12 + bootstrap owner +
   composite-unique + фикс дрейфа.
2. `feat-owner-scope-repos` — конструктор-скоп в `BaseRepository` + 21 репо +
   `get_current_user` + плампинг в роутерах.
3. `feat-owner-background-services` — owner-резолв в PollService/restore_channels/AI/адаптерах.
4. `feat-per-owner-seed` — `seed_version` + переписанные seed-функции под `(owner_id, slug)`.
5. `feat-offline-owner-scope` — IndexedDB v4 + persister + query-keys + sync-очередь по owner.
6. `feat-owner-export` — per-owner export/import.
7. `test-owner-scope-gates` — gating-тест на фильтр owner_id + негативные сценарии + тесты миграций.

## Ссылки на источники в коде

`backend/app/models/*.py` (21 файл) · `backend/app/repositories/base.py` ·
`backend/app/services/migration_service.py` · `backend/app/database.py` ·
`backend/app/routers/export.py` · `backend/seed.py` · `backend/app/config.py` ·
`frontend/src/offline/{db,queue,sync,merge,queryClient}.ts` ·
`frontend/src/api/client.ts` · `frontend/src/App.tsx` · `frontend/src/hooks/queries.ts`
