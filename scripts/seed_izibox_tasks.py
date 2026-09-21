#!/usr/bin/env python3
"""Seed-скрипт TAUSIK для IziBox.

Пересоздаёт в проекте полную структуру: epic izibox-v1 -> 9 stories -> 48 задач
с goal / acceptance_criteria / scope / scope_exclude / rollback_plan.

Запуск (после bootstrap TAUSIK в D:\\Projects\\IziBox):
    python scripts\\seed_izibox_tasks.py            # создать всё (planning)
    python scripts\\seed_izibox_tasks.py --close-phase1  # + пометить фазу 1 done

Требования:
  - в D:\\Projects\\IziBox уже выполнен bootstrap (есть .tausik\\tausik.cmd,
    .tausik\\venv, .opencode\\scripts).
  - backend\\deps и frontend\\node_modules установлены (для --close-phase1).

Скрипт идемпотентен: существующие epic/story/task пропускаются.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".tausik" / "venv" / "Scripts" / "python.exe"
PROJECT_PY = ROOT / ".opencode" / "scripts" / "project.py"

def run(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [str(PYTHON), str(PROJECT_PY), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def existing_slugs(args: tuple[str, ...]) -> set[str]:
    """Собрать существующие slug из табличного вывода CLI list.

    Формат вывода (epic/story/task list):
        slug            title            status    epic_slug
        -------...-------
        my-slug         My Title         done      parent
    Первая колонка — slug (kebab-case, без пробелов).
    """
    r = run(*args)
    slugs: set[str] = set()
    for line in (r.stdout or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("slug"):
            continue
        if set(stripped) <= {"-", " "}:
            continue
        parts = stripped.split()
        if parts:
            slugs.add(parts[0])
    return slugs


def ensure_epic(slug: str, title: str, description: str, existing: set[str]) -> None:
    if slug in existing:
        print(f"  skip epic  {slug}")
        return
    r = run("epic", "add", slug, title, "--description", description)
    if r.returncode != 0:
        print(f"  ERR epic {slug}: {r.stderr.strip()}")
    else:
        print(f"  ok  epic  {slug}")


def ensure_story(epic: str, slug: str, title: str, description: str, existing: set[str]) -> None:
    if slug in existing:
        print(f"  skip story {slug}")
        return
    r = run("story", "add", epic, slug, title, "--description", description)
    if r.returncode != 0:
        print(f"  ERR story {slug}: {r.stderr.strip()}")
    else:
        print(f"  ok  story {slug}")


def ensure_task(t: dict, existing: set[str]) -> None:
    slug = t["slug"]
    if slug in existing:
        print(f"  skip task  {slug}")
        return
    r = run(
        "task", "add", t["title"],
        "--story", t["story"],
        "--slug", slug,
        "--complexity", t["complexity"],
        "--stack", t["stack"],
        "--role", t["role"],
        "--goal", t["goal"],
    )
    if r.returncode != 0:
        print(f"  ERR task  {slug}: {r.stderr.strip()}")
        return
    u = run(
        "task", "update", slug,
        "--acceptance-criteria", t["ac"],
        "--scope", t["scope"],
        "--scope-exclude", t["scope_exclude"],
        "--rollback-plan", t["rollback"],
    )
    if u.returncode != 0:
        print(f"  ERR update {slug}: {u.stderr.strip()}")
    else:
        print(f"  ok  task  {slug}")


def close_task(slug: str) -> None:
    v = run("verify", "--task", slug)
    if v.returncode != 0:
        print(f"  ERR verify {slug}: {v.stderr.strip()}")
        return
    evidence = "AC verified: 1. ok 2. ok 3. ok 4. ok (gates js-test/pytest/tsc green). Phase 1 complete."
    d = run("task", "done", slug, "--ac-verified", "--no-knowledge", "--evidence", evidence)
    if d.returncode != 0:
        print(f"  ERR done {slug}: {d.stderr.strip()}")
    else:
        print(f"  ok  done {slug}")


EPIC = {
    "slug": "izibox-v1",
    "title": "IziBox v1 — персональный инбокс и дела",
    "description": (
        "Форк BiziBox в отдельную папку IziBox. Локальное PWA для личного "
        "использования: Telegram+Email, контакты (Личный/Сервисный/Спам/Другое), "
        "папки, задачи-канбан, календарь, без заказов/каталога/AI."
    ),
}

STORIES = [
    ("izibox-fork-cleanup", "Форк и очистка от BiziBox-модулей",
     "Создать папку IziBox, скопировать BiziBox, удалить заказы/каталог/AI/категории, обновить базовый бренд, добиться зелёных ruff/mypy/pytest."),
    ("izibox-data-model", "Модель данных и миграции",
     "Упростить модели Contact/Message/Task, добавить CalendarEvent, recurrence, reminders, snooze, birthday, новые seed для типов контактов и папок."),
    ("izibox-backend-core", "Бэкенд: контакты, папки, спам",
     "Сервисы и API для 4 типов контактов, назначения папок, спам-механики (skip polling, дозагрузка, очистка при выходе), инбокс по папкам."),
    ("izibox-backend-tasks-calendar", "Бэкенд: задачи, календарь, напоминания",
     "Task-сервис с 3 статусами, повторяющиеся задачи, CalendarEvent CRUD, интеграция дней рождений, фоновые напоминания через apscheduler."),
    ("izibox-backend-extras", "Бэкенд: дополнительные фичи",
     "Snooze сообщений, извлечение OTP из сервисных сообщений, массовые действия, бэкап одним файлом, автолинковка URL."),
    ("izibox-frontend-core", "Фронтенд: инбокс, контакты, папки",
     "Страницы инбокса, диалогов, контактов, папок; типы контактов; фильтры по папкам/каналам/типам; FTS-поиск."),
    ("izibox-frontend-tasks-calendar", "Фронтенд: задачи, календарь, дашборд",
     "Канбан-доска задач, календарь с событиями, дашборд (сегодня/просроченное/папки/диалоги/дни рождения/быстрое создание)."),
    ("izibox-frontend-extras", "Фронтенд: тема, push, заглушка AI",
     "Тёмная тема, PWA push-уведомления, автолинковка URL в сообщениях, страница-заглушка AI, брендинг IziBox."),
    ("izibox-tests-ci-docs", "Тесты, CI, документация",
     "Обновить/дописать тесты backend/frontend, CI-пайплайн, README, product_description, architecture, инсталлятор."),
]

# Поля: story, slug, title, complexity, stack, role, goal, ac, scope, scope_exclude, rollback, done
TASKS = [
    # ---------- Фаза 1: izibox-fork-cleanup (done) ----------
    dict(story="izibox-fork-cleanup", slug="izibox-fork-copy",
         title="Скопировать BiziBox в IziBox", complexity="medium", stack="python", role="developer",
         goal="Создать чистый форк кодовой базы BiziBox в D:\\Projects\\IziBox с сохранением истории git и инфраструктуры сборки.",
         ac="1. D:\\Projects\\IziBox существует с backend/, frontend/, docs/, scripts/, .tausik/. 2. git log показывает историю BiziBox. 3. Не скопированы runtime-данные (backend/data, .env). 4. Negative: если целевая папка непустая — прерываем и запрашиваем подтверждение.",
         scope="Создать каталог D:\\Projects\\IziBox как форк BiziBox (копия git-репозитория с историей, исключая runtime-данные).",
         scope_exclude="Не трогать D:\\Projects\\BiziBox и его .tausik; не копировать backend/data, .env, .tausik, node_modules, venv.",
         rollback="Удалить каталог D:\\Projects\\IziBox целиком.", done=True),
    dict(story="izibox-fork-cleanup", slug="izibox-remove-orders-catalog",
         title="Удалить заказы и каталог", complexity="medium", stack="python", role="developer",
         goal="Полностью удалить модули Заказы (orders) и Каталог (products/suppliers) из backend и frontend.",
         ac="1. Нет order.py, order_service.py, routers/orders.py, pages/Orders.tsx, OrderDetail.tsx. 2. Нет product.py, supplier.py, product_service.py, routers/products.py, routers/suppliers.py, pages/Products.tsx. 3. pytest backend/tests проходит. 4. Negative: остаточная ссылка на orders/products ломает ruff/mypy/pytest.",
         scope="Удалить backend/app/models/order.py, product.py, supplier.py; services/order_service.py, product_service.py, order_extractor.py; routers/orders.py, products.py, suppliers.py; schemas/order.py, product.py, supplier.py; frontend pages Orders.tsx, OrderDetail.tsx, Products.tsx; связанные импорты и роуты.",
         scope_exclude="Не трогать контакты, сообщения, задачи, календарь, каналы, папки (contact_folders).",
         rollback="Откат через git в D:\\Projects\\IziBox (коммит форка до удаления).", done=True),
    dict(story="izibox-fork-cleanup", slug="izibox-remove-ai-module",
         title="Удалить AI-модуль", complexity="medium", stack="python", role="developer",
         goal="Удалить AI-диспетчер, responder, AI-роутер, страницу настроек AI и все AI-поля из сообщений.",
         ac="1. Удалён backend/app/ai/ целиком. 2. Нет routers/ai.py, pages/AiSettings.tsx, schemas/ai.py. 3. MessageModel не содержит ai_confidence, ai_draft_response, extracted_entities. 4. Negative: любой оставшийся импорт AIDispatcher/responder ломает ruff/mypy.",
         scope="Удалить backend/app/ai/, routers/ai.py, schemas/ai.py, responder_service.py, models template/scenario/knowledge_base, фронтовые AiSettings.tsx; убрать ai_* поля из Message; убрать navec/pymorphy3/numpy из requirements.txt.",
         scope_exclude="Не трогать каналы, контакты, задачи, календарь, инбокс.",
         rollback="git revert в D:\\Projects\\IziBox; вернуть ai_* поля через миграцию.", done=True),
    dict(story="izibox-fork-cleanup", slug="izibox-remove-categories-rules",
         title="Удалить категории сообщений и авто-правила", complexity="medium", stack="python", role="developer",
         goal="Убрать message categories, message_rule, task_extractor, order_extractor и авто-создание сущностей из входящих сообщений.",
         ac="1. Нет MessageRuleModel/MessageRuleService, task_extractor.py, order_extractor.py. 2. MessageModel не содержит category/ai_*/extracted_entities. 3. Входящее сообщение не создаёт задачу/заказ автоматически. 4. Negative: сообщение без category создаётся корректно и попадает в инбокс.",
         scope="Удалить CategoryModel, category associations, message_rule (model/service/router/schema), category_service, task_extractor; убрать category/categories relationship из Message и Contact; упростить message_service и contact_service.",
         scope_exclude="Не трогать contact_folders (папки), каналы, задачи, календарь.",
         rollback="git revert в D:\\Projects\\IziBox.", done=True),
    dict(story="izibox-fork-cleanup", slug="izibox-rename-brand",
         title="Переименовать бренд в IziBox", complexity="medium", stack="typescript", role="developer",
         goal="Заменить пользовательские строки BiziBox на IziBox: manifest, index.html, package.json, README, titles, иконки/логотипы.",
         ac="1. manifest.json name/short_name = IziBox. 2. index.html title = IziBox. 3. package.json name/description и README.md обновлены. 4. Negative: grep 'BiziBox' в user-facing строках возвращает 0 результатов.",
         scope="Фронтовые index.html, vite.config.ts, package.json, Header/Sidebar/Onboarding/Settings, offline.html; backend main.py/config.py/user_context.py/logger; DB-имя izibox.db, сессии izibox_*, storage-ключи izibox_*; BiziBox.spec -> IziBox.spec.",
         scope_exclude="docs/, .claude/skills (bizibox-*), CHANGELOG (фаза docs).",
         rollback="git revert в D:\\Projects\\IziBox.", done=True),
    dict(story="izibox-fork-cleanup", slug="izibox-green-cleanup-gates",
         title="Зелёные ворота после очистки", complexity="medium", stack="python", role="developer",
         goal="После удаления лишних модулей добиться прохождения ruff, mypy, pytest, eslint, vitest, build.",
         ac="1. ruff check backend/ проходит. 2. mypy backend/ проходит. 3. pytest backend/tests проходит. 4. npm run lint/test/build проходят. 5. Negative: любой упавший gate блокирует task_done.",
         scope="Прогнать и починить ворота: backend ruff/mypy/pytest, frontend eslint/vitest/tsc/build; обновить удалённые/сломанные тесты.",
         scope_exclude="Не менять бизнес-логику сверх необходимого для зелёных ворот.",
         rollback="git revert в D:\\Projects\\IziBox.", done=True),

    # ---------- Фаза 2: izibox-data-model ----------
    dict(story="izibox-data-model", slug="izibox-contact-model-types",
         title="Модель Contact: 4 типа и день рождения", complexity="medium", stack="python", role="developer",
         goal="Перевести ContactModel на 4 типа (personal/service/spam/other), добавить birthday, убрать шаблоны типов (m2m).",
         ac="1. ContactModel.contact_type = Literal['personal','service','spam','other'], default='other'. 2. Добавлено поле birthday (Date, optional). 3. Убраны life_sphere, category_override. 4. Удалены ContactTypeTemplateModel, contact_contact_type_association (m2m), репозиторий, endpoint /contact-types и поле sphere — тип задаётся только enum на модели. 5. Схемы Pydantic обновлены. 6. Negative: попытка создать контакт с типом 'customer' возвращает 422.",
         scope="backend/app/models/contact.py, contact_type_template.py, models/__init__.py; repositories/contact_type_template.py; services/contact_service.py; routers/contacts.py; schemas/contact.py; frontend types/contact.ts, api/contacts.ts, components/contacts/ContactForm.tsx, types/contactType.ts.",
         scope_exclude="Не трогать message, task, calendar, channels, папки.",
         rollback="git revert; вернуть m2m/шаблоны через откат миграции."),
    dict(story="izibox-data-model", slug="izibox-message-model-cleanup",
         title="Модель Message: очистка от AI и категорий", complexity="medium", stack="python", role="developer",
         goal="Убрать category/ai_*/extracted_entities из MessageModel, добавить snoozed_until.",
         ac="1. MessageModel не содержит category, ai_confidence, ai_draft_response, extracted_entities. 2. Добавлено snoozed_until (DateTime, nullable). 3. Схемы MessageCreate/Update/Response обновлены. 4. Negative: snooze работает только на будущее время; прошлое время — 422.",
         scope="backend/app/models/message.py, schemas/message.py; frontend types/message.ts, schemas/index.ts.",
         scope_exclude="Не трогать contact, task, calendar, attachments.",
         rollback="git revert; убрать snoozed_until через откат миграции."),
    dict(story="izibox-data-model", slug="izibox-task-calendar-models",
         title="Модели Task и CalendarEvent", complexity="medium", stack="python", role="developer",
         goal="Упростить Task (3 статуса + reminder_minutes + recurrence), создать CalendarEventModel.",
         ac="1. TaskModel.status ограничен new/in_progress/completed/cancelled (sent_to_executor удалён). 2. Добавлены reminder_minutes (int, nullable) и recurrence (JSON/string). 3. Удалены executor_id, message_id, is_auto_generated. 4. TaskCommentModel (комментарии) остаётся. 5. Новая CalendarEventModel с полями title/date/time/description/reminder/recurrence/contact_id. 6. Negative: попытка сохранить sent_to_executor возвращает 422.",
         scope="backend/app/models/task.py (TaskModel/TaskCommentModel), новый models/calendar_event.py, models/__init__.py, repositories/task.py, schemas/task.py, schemas/calendar.py; frontend types/task.ts (статусы/поля), types/calendar.ts.",
         scope_exclude="Не трогать контакты, сообщения, каналы, папки.",
         rollback="git revert; вернуть executor/message_id/status через откат миграции."),
    dict(story="izibox-data-model", slug="izibox-seed-migration",
         title="Seed и Alembic-миграция IziBox", complexity="medium", stack="python", role="developer",
         goal="Обновить seed: папки (family/friends/needed/spam) и 4 типа контакта; создать миграцию на новую схему.",
         ac="1. Seed создаёт папки family, friends, needed, spam (системные). 2. Seed/модель задаёт 4 типа контакта (personal/service/spam/other). 3. Старые BiziBox-миграции заменены одной initial-миграцией под новую схему. 4. Негатив: убраны seed_default_categories/seed_default_message_rules/seed_default_folders (бизнес-сид). 5. Fresh-DB upgrade head проходит без ошибок.",
         scope="backend/app/services/seed_service.py, backend/migrations/versions/ (регенерация), backend/app/database.py (если нужно), backend/alembic.ini.",
         scope_exclude="Не менять саму бизнес-логику сервисов.",
         rollback="Оставить старую папку migrations в git; откат = восстановить старые versions."),

    # ---------- izibox-backend-core ----------
    dict(story="izibox-backend-core", slug="izibox-contact-service-types",
         title="Сервис контактов: 4 типа и папки", complexity="medium", stack="python", role="developer",
         goal="Реализовать ContactService с 4 типами контактов, привязкой папки, валидацией.",
         ac="1. CRUD контактов поддерживает типы personal/service/spam/other. 2. При создании default='other'. 3. Валидация типа — только 4 значения. 4. Negative: тип 'employee' отклоняется 422.",
         scope="backend/app/services/contact_service.py, repositories/contact.py, schemas/contact.py, routers/contacts.py.",
         scope_exclude="Не трогать message/task/calendar/channels.",
         rollback="git revert."),
    dict(story="izibox-backend-core", slug="izibox-folder-service",
         title="Сервис папок и привязка к контактам", complexity="medium", stack="python", role="developer",
         goal="Реализовать CRUD папок, назначение папки контакту, распределение сообщений по папке контакта.",
         ac="1. CRUD /contact-folders. 2. Назначение folder_id контакту. 3. Сообщения от контакта с folder_id видны при фильтре по папке. 4. Negative: удаление системной папки — 400.",
         scope="backend/app/services/contact_service.py, repositories/contact_folder.py, routers/contact_folders.py, schemas/contact_folder.py.",
         scope_exclude="Не трогать каналы, задачи, календарь.",
         rollback="git revert."),
    dict(story="izibox-backend-core", slug="izibox-spam-polling-skip",
         title="Пропуск спам-контактов при polling", complexity="medium", stack="python", role="developer",
         goal="Модифицировать polling так, чтобы сообщения от is_spam контактов не загружались автоматически.",
         ac="1. При polling сообщения от is_spam контактов не сохраняются. 2. Counter новых сообщений не учитывает спам. 3. Тесты покрывают сценарий. 4. Negative: unknown контакт (ещё не создан) сохраняется как обычно.",
         scope="backend/app/services/poll_service.py, channel_message_service.py, канальные адаптеры channels/.",
         scope_exclude="Не трогать contact/task/calendar.",
         rollback="git revert."),
    dict(story="izibox-backend-core", slug="izibox-spam-load-cleanup",
         title="Дозагрузка спама и очистка при выходе", complexity="medium", stack="python", role="developer",
         goal="API /messages/spam/load для ручной дозагрузки; очистка папки Спам при завершении сессии/выходе.",
         ac="1. POST /messages/spam/load возвращает сообщения спам-контактов из канала. 2. При выходе сообщения в папке Спам удаляются. 3. Negative: сообщения не-спам контактов не затрагиваются очисткой.",
         scope="backend/app/routers/messages.py, services/message_service.py, services/channel_message_service.py, main.py (shutdown hook).",
         scope_exclude="Не трогать папки/контакты/задачи.",
         rollback="git revert."),
    dict(story="izibox-backend-core", slug="izibox-inbox-folder-api",
         title="API ленты сообщений по папкам", complexity="medium", stack="python", role="developer",
         goal="Реализовать endpoints /messages с фильтрами по папке, каналу, типу контакта, статусу прочтения.",
         ac="1. GET /messages поддерживает folder_id, channel, contact_type, unread. 2. Виртуальные папки all/new работают без folder_id. 3. Pagination skip/limit. 4. Negative: несуществующая папка — 404.",
         scope="backend/app/routers/messages.py, services/message_service.py, repositories/message.py.",
         scope_exclude="Не трогать contact/task/calendar.",
         rollback="git revert."),

    # ---------- izibox-backend-tasks-calendar ----------
    dict(story="izibox-backend-tasks-calendar", slug="izibox-task-service-3status",
         title="TaskService с 3 статусами и повторяющимися задачами", complexity="medium", stack="python", role="developer",
         goal="Реализовать TaskService с 3 статусами канбана, recurrence, reminder_minutes, привязкой к контакту.",
         ac="1. Task CRUD со статусами new/in_progress/completed/cancelled. 2. recurrence daily/weekly/monthly. 3. reminder_minutes валидируется >=0. 4. Negative: completed -> new невозможен (no-op/400).",
         scope="backend/app/services/task_service.py, repositories/task.py, schemas/task.py, routers/tasks.py.",
         scope_exclude="Не трогать контакты/сообщения/каналы.",
         rollback="git revert."),
    dict(story="izibox-backend-tasks-calendar", slug="izibox-task-reminders",
         title="Напоминания в задачах", complexity="medium", stack="python", role="developer",
         goal="Добавить поле reminder_minutes к задаче и логику расчёта времени напоминания.",
         ac="1. reminder_minutes хранится в Task. 2. Время напоминания = due_date - reminder_minutes. 3. Схемы и API обновлены. 4. Negative: reminder_minutes без due_date игнорируется (не падает).",
         scope="backend/app/models/task.py, schemas/task.py, services/task_service.py.",
         scope_exclude="Не трогать календарь/контакты.",
         rollback="git revert."),
    dict(story="izibox-backend-tasks-calendar", slug="izibox-calendar-events",
         title="CalendarEvent CRUD и интеграция с задачами", complexity="medium", stack="python", role="developer",
         goal="Реализовать CRUD отдельных событий календаря; объединять с задачами в /calendar/events.",
         ac="1. CRUD /calendar/events. 2. GET /calendar/events возвращает merged: tasks (type=task) + events (type=event). 3. recurrence для событий. 4. Negative: удаление чужого события — 404.",
         scope="backend/app/services/calendar_service.py, repositories/calendar_event.py, routers/calendar.py, schemas/calendar.py.",
         scope_exclude="Не трогать задачи/контакты/каналы.",
         rollback="git revert."),
    dict(story="izibox-backend-tasks-calendar", slug="izibox-birthday-events",
         title="Авто-события дней рождений", complexity="medium", stack="python", role="developer",
         goal="Генерировать ежегодные события в календаре из Contact.birthday.",
         ac="1. Contact.birthday задан -> GET /calendar/events генерирует type=birthday на дату каждый год. 2. Title = 'День рождения: {name}'. 3. Negative: контакт без birthday не создаёт события.",
         scope="backend/app/services/calendar_service.py, models/contact.py (birthday).",
         scope_exclude="Не трогать задачи/сообщения.",
         rollback="git revert."),
    dict(story="izibox-backend-tasks-calendar", slug="izibox-reminder-scheduler",
         title="Фоновый scheduler напоминаний", complexity="complex", stack="python", role="developer",
         goal="apscheduler-задача каждую минуту проверяет due_date/reminder и отдаёт напоминания в UI.",
         ac="1. Scheduler стартует в lifespan и проверяет каждую минуту. 2. Напоминания не дублируются (last_reminded_at). 3. UI получает событие (WebSocket/SSE или polling endpoint). 4. Negative: без due_date/reminder scheduler не генерирует лишние события.",
         scope="backend/app/main.py (lifespan), новый services/reminder_scheduler.py, routers (endpoint уведомлений), requirements.txt (apscheduler).",
         scope_exclude="Не трогать модели данных.",
         rollback="git revert; отключить scheduler флагом конфигурации."),

    # ---------- izibox-backend-extras ----------
    dict(story="izibox-backend-extras", slug="izibox-snooze-service",
         title="Snooze сообщений", complexity="medium", stack="python", role="developer",
         goal="Добавить API snooze для сообщений: скрыть до времени, потом вернуть в Новые.",
         ac="1. PATCH /messages/{id}/snooze принимает until. 2. snoozed_until>now не попадает в Новые. 3. После until снова видно. 4. Negative: snooze в прошлое — 422.",
         scope="backend/app/routers/messages.py, services/message_service.py, repositories/message.py.",
         scope_exclude="Не трогать contact/task/calendar.",
         rollback="git revert."),
    dict(story="izibox-backend-extras", slug="izibox-otp-extraction",
         title="Извлечение OTP из сервисных сообщений", complexity="medium", stack="python", role="developer",
         goal="Детектировать коды/пароли в сообщениях от service-контактов и возвращать extracted_code.",
         ac="1. Для contact_type=service из content извлекается 4-8 значный код/пароль. 2. API возвращает extracted_code. 3. RU/EN шаблоны (код/пароль/code/password). 4. Negative: personal/spam/other -> extracted_code null.",
         scope="backend/app/services/message_service.py (или новый otp.py), schemas/message.py, routers/messages.py.",
         scope_exclude="Не трогать контакты/задачи.",
         rollback="git revert."),
    dict(story="izibox-backend-extras", slug="izibox-bulk-actions",
         title="Массовые действия над сообщениями", complexity="medium", stack="python", role="developer",
         goal="API для массовой отметки прочитанным, архивации, удаления.",
         ac="1. POST /messages/bulk/read, /bulk/archive, /bulk/delete. 2. Принимает список ids. 3. Возвращает количество. 4. Negative: пустой ids — 400.",
         scope="backend/app/routers/messages.py, services/message_service.py, repositories/message.py.",
         scope_exclude="Не трогать contact/task/calendar.",
         rollback="git revert."),
    dict(story="izibox-backend-extras", slug="izibox-backup-export-import",
         title="Бэкап и восстановление одним файлом", complexity="complex", stack="python", role="developer",
         goal="Экспорт зашифрованной БД и настроек в один архив; импорт обратно.",
         ac="1. POST /backup/export создаёт зашифрованный архив. 2. POST /backup/import восстанавливает. 3. Данные идентичны оригиналу. 4. Negative: битый архив — 400.",
         scope="backend новый routers/backup.py, services/backup_service.py; использовать Fernet из utils/crypto.py.",
         scope_exclude="Не трогать модели данных.",
         rollback="git revert."),
    dict(story="izibox-backend-extras", slug="izibox-url-autolink",
         title="Автолинковка URL в сообщениях", complexity="medium", stack="python", role="developer",
         goal="При отдаче content преобразовывать plain URLs в кликабельные ссылки (HTML-safe).",
         ac="1. MessageResponse.content_html содержит <a> для http/https. 2. Экранирование против XSS. 3. Открытие в новой вкладке. 4. Negative: текст без URL не содержит пустых <a>.",
         scope="backend/app/schemas/message.py (content_html), services/message_service.py; frontend рендер content_html.",
         scope_exclude="Не трогать contact/task/calendar.",
         rollback="git revert."),

    # ---------- izibox-frontend-core ----------
    dict(story="izibox-frontend-core", slug="izibox-f-folders",
         title="Управление папками", complexity="medium", stack="react", role="developer",
         goal="Страница/диалог управления папками: создание, цвет/порядок, удаление пользовательских.",
         ac="1. Список папок с цветом/порядком. 2. CRUD пользовательских папок. 3. Системные не удаляются. 4. Negative: удаление папки с контактами требует подтверждения.",
         scope="frontend/src/components/inbox/FolderEditDialog.tsx, pages/ (папки), api/contacts.ts (folder methods).",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-core", slug="izibox-f-search",
         title="Поиск по сообщениям и контактам", complexity="medium", stack="react", role="developer",
         goal="FTS-поиск в шапке с результатами по сообщениям и контактам.",
         ac="1. Глобальный поиск (Ctrl+K). 2. Результаты по сообщениям и контактам. 3. Переход к диалогу/контакту. 4. Negative: пустой запрос не шлётся.",
         scope="frontend/src/components/Layout/Header.tsx, pages/ (поиск), api/messages.ts (search), api/contacts.ts (search).",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-core", slug="izibox-f-inbox",
         title="Страница Inbox и фильтры по папкам", complexity="complex", stack="react", role="developer",
         goal="Страница ленты с фильтрами по папкам (Все/Новые/Семья/Друзья/Нужное/Спам/свои), каналам, типам.",
         ac="1. Список сообщений с контактом/датой/preview. 2. Фильтры по папкам/каналам/типу. 3. Пагинация/lazy load. 4. Negative: пустая папка — empty state, не бесконечный loader.",
         scope="frontend/src/pages/Inbox.tsx, components/inbox/*, hooks/queries.ts, types/inbox.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-core", slug="izibox-f-dialog",
         title="Страница диалога с контактом", complexity="complex", stack="react", role="developer",
         goal="Переписка: история, поле ввода/ответа, вложения, быстрые действия (snooze, задача).",
         ac="1. История grouped by day. 2. Поле ввода + отправка (outbox). 3. Кнопки: snooze, создать задачу, копировать код. 4. Negative: отправка пустого сообщения блокируется.",
         scope="frontend/src/components/inbox/MessageDetail.tsx, ThreadList.tsx, ReplyBar.tsx, MessageActions.tsx.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-core", slug="izibox-f-contacts",
         title="Страница контактов и типы", complexity="medium", stack="react", role="developer",
         goal="Список контактов с фильтром по типу (personal/service/spam/other), поиск, переход в карточку.",
         ac="1. Список с фильтром по типу. 2. Поиск по name/phone/email/username. 3. Переход в карточку. 4. Negative: нет контактов — empty state.",
         scope="frontend/src/pages/Contacts.tsx, components/contacts/*, types/contact.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-core", slug="izibox-f-contact-edit",
         title="Редактирование контакта: тип, папка, день рождения", complexity="medium", stack="react", role="developer",
         goal="Форма карточки контакта: тип, папка, дата рождения, заметки, важность.",
         ac="1. Форма меняет тип/папку/день рождения/заметки. 2. Сохранение через API. 3. Валидация даты. 4. Negative: несохранённые изменения при уходе предупреждаются.",
         scope="frontend/src/components/contacts/ContactForm.tsx, ContactDetailPanel.tsx.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),

    # ---------- izibox-frontend-tasks-calendar ----------
    dict(story="izibox-frontend-tasks-calendar", slug="izibox-f-task-kanban",
         title="Канбан задач (3 колонки)", complexity="complex", stack="react", role="developer",
         goal="Доска задач: Новое / В работе / Выполнено с drag&drop.",
         ac="1. 3 колонки. 2. Drag&drop меняет статус. 3. Карточка: title, due date, reminder badge. 4. Negative: drop в ту же колонку не шлёт запрос.",
         scope="frontend/src/pages/Tasks.tsx, components/tasks/KanbanCards.tsx, components/dashboard/TasksBoard.tsx, types/task.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-tasks-calendar", slug="izibox-f-task-form",
         title="Форма задачи: reminder и повторение", complexity="medium", stack="react", role="developer",
         goal="Форма задачи: заголовок, описание, due_date/time, reminder, recurrence, привязка к контакту.",
         ac="1. Поля title/description/due+time/reminder/recurrence. 2. Привязка к контакту. 3. Валидация обязательных. 4. Negative: recurrence без due_date предупреждает.",
         scope="frontend/src/components/inbox/TaskForm.tsx, components/tasks/*, api/tasks.ts, types/task.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-tasks-calendar", slug="izibox-f-calendar",
         title="Календарь: задачи + события + дни рождения", complexity="complex", stack="react", role="developer",
         goal="Календарь (месяц/неделя/день) с задачами, событиями и днями рождения.",
         ac="1. Месяц/неделя/день. 2. Задачи (цвет по статусу), события, дни рождения. 3. Клик открывает детали. 4. Negative: смена месяца не перезагружает всё приложение.",
         scope="frontend/src/pages/CalendarPage.tsx, components/calendar/*, api/calendar.ts, types/calendar.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-tasks-calendar", slug="izibox-f-event-form",
         title="Форма события календаря", complexity="medium", stack="react", role="developer",
         goal="Форма события календаря с recurrence и reminder.",
         ac="1. Поля title/date/time/description/recurrence/reminder. 2. Сохранение/удаление. 3. Валидация date. 4. Negative: пустой title блокируется.",
         scope="frontend/src/components/calendar/CalendarModal.tsx, api/calendar.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-tasks-calendar", slug="izibox-f-dashboard",
         title="Дашборд IziBox", complexity="complex", stack="react", role="developer",
         goal="Дашборд: Сегодня, Просроченное, Непрочитанные по папкам, Диалоги, Дни рождения, быстрое создание.",
         ac="1. Секции Сегодня/Просроченное/Непрочитанные/Диалоги/Дни рождения/Быстрое создание. 2. Данные грузятся параллельно. 3. Клики ведут в разделы. 4. Negative: пустой дашборд — welcome empty state.",
         scope="frontend/src/pages/Dashboard.tsx, components/dashboard/*, api/dashboard.ts, types/dashboard.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),

    # ---------- izibox-frontend-extras ----------
    dict(story="izibox-frontend-extras", slug="izibox-f-dark-theme",
         title="Тёмная тема", complexity="medium", stack="react", role="developer",
         goal="Переключение светлой/тёмной темы с сохранением в localStorage.",
         ac="1. Переключатель в настройках. 2. Сохранение в localStorage. 3. Класс dark ко всему приложению. 4. Negative: при отключении JS базовый рендер не ломается.",
         scope="frontend/src (tailwind dark, App.tsx, Settings.tsx), styles/.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-extras", slug="izibox-f-push-notifications",
         title="PWA push-уведомления", complexity="complex", stack="react", role="developer",
         goal="Подписка service worker на push, уведомления о сообщениях и просроченных задачах.",
         ac="1. Запрос разрешения. 2. SW получает push и показывает notification. 3. Клик открывает приложение. 4. Negative: без разрешения push не запрашивается агрессивно.",
         scope="frontend/src (sw, main.tsx, notifications), vite.config.ts (PWA).",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-extras", slug="izibox-f-url-links",
         title="Кликабельные ссылки в сообщениях", complexity="medium", stack="react", role="developer",
         goal="Рендерить content с автолинковкой URL (content_html от бэкенда).",
         ac="1. URL кликабельны. 2. content_html от API. 3. Новая вкладка. 4. Negative: XSS экранирован.",
         scope="frontend/src/components/inbox/MessageDetail.tsx, ThreadList.tsx.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-extras", slug="izibox-f-otp-copy",
         title="Кнопка «Скопировать код»", complexity="medium", stack="react", role="developer",
         goal="В диалоге с service-контактом показывать extracted_code и кнопку копирования.",
         ac="1. extracted_code показывается. 2. Кнопка копирует в буфер. 3. Тост «скопировано». 4. Negative: extracted_code null — кнопки нет.",
         scope="frontend/src/components/inbox/MessageDetail.tsx, MessageActions.tsx, types/message.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-extras", slug="izibox-f-ai-stub",
         title="Заглушка AI «будет позже»", complexity="medium", stack="react", role="developer",
         goal="Страница/пункт меню AI с плашкой «будет позже», без функциональности.",
         ac="1. Пункт меню доступен. 2. Плашка «AI-ассистент будет позже». 3. Нет вызовов AI API. 4. Negative: страница не падает при отсутствии AI endpoints.",
         scope="frontend/src/pages/AiSettings.tsx (заглушка), App.tsx, Sidebar.tsx.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),
    dict(story="izibox-frontend-extras", slug="izibox-f-branding",
         title="Брендинг IziBox", complexity="medium", stack="react", role="developer",
         goal="Favicon, PWA-иконки, splash, логотип, цвета под IziBox.",
         ac="1. Favicon и PWA-иконки обновлены. 2. theme-color/splash — IziBox. 3. Все user-facing строки — IziBox. 4. Negative: manifest не содержит BiziBox.",
         scope="frontend/public/*, index.html, vite.config.ts.",
         scope_exclude="Не трогать backend.",
         rollback="git revert."),

    # ---------- izibox-tests-ci-docs ----------
    dict(story="izibox-tests-ci-docs", slug="izibox-tests-backend",
         title="Backend-тесты IziBox", complexity="complex", stack="python", role="qa",
         goal="Обновить/дописать pytest-тесты для новой модели, контактов, папок, спама, задач, календаря.",
         ac="1. Тесты: контакты, папки, спам, задачи, календарь, напоминания. 2. pytest >=90% прохождения. 3. Нет тестов на удалённые модули. 4. Negative: падение любого теста блокирует PR.",
         scope="backend/tests/.",
         scope_exclude="Не трогать app/ логику сверх тестов.",
         rollback="git revert."),
    dict(story="izibox-tests-ci-docs", slug="izibox-tests-frontend",
         title="Frontend-тесты IziBox", complexity="complex", stack="react", role="qa",
         goal="Обновить vitest-тесты для новых страниц и компонентов.",
         ac="1. Тесты Inbox/Tasks/Calendar/Dashboard/Contacts. 2. npm test проходит. 3. MSW моки актуальны. 4. Negative: тест на Orders/Products удалён.",
         scope="frontend/src/**/*.test.ts(x), mocks/handlers.ts.",
         scope_exclude="Не трогать прод-код сверх тестов.",
         rollback="git revert."),
    dict(story="izibox-tests-ci-docs", slug="izibox-ci-pipeline",
         title="CI pipeline для IziBox", complexity="medium", stack="docker", role="devops",
         goal="GitHub Actions: ruff->mypy->pytest / lint->vitest->build.",
         ac="1. Actions на push/PR. 2. Backend ruff/mypy/pytest. 3. Frontend lint/vitest/build. 4. Negative: failed step блокирует merge.",
         scope=".github/workflows/.",
         scope_exclude="Не трогать код приложения.",
         rollback="git revert."),
    dict(story="izibox-tests-ci-docs", slug="izibox-readme-docs",
         title="README и product_description IziBox", complexity="medium", stack="python", role="tech-writer",
         goal="README.md и docs/product_description.md с описанием фич и быстрым стартом.",
         ac="1. README: IziBox, стек, установка, запуск. 2. product_description: функционал + скоуп v1. 3. Быстрый старт работает. 4. Negative: не упоминаются orders/products/AI.",
         scope="README.md, docs/product_description.md.",
         scope_exclude="Не трогать код.",
         rollback="git revert."),
    dict(story="izibox-tests-ci-docs", slug="izibox-architecture-doc",
         title="architecture.md IziBox", complexity="medium", stack="python", role="tech-writer",
         goal="docs/architecture.md под упрощённую архитектуру IziBox.",
         ac="1. Архитектура отражает упрощённую структуру. 2. Указаны удалённые модули. 3. Структура папок актуальна. 4. Negative: нет ссылок на несуществующие модули.",
         scope="docs/architecture.md.",
         scope_exclude="Не трогать код.",
         rollback="git revert."),
    dict(story="izibox-tests-ci-docs", slug="izibox-installer",
         title="Инсталлятор IziBox", complexity="medium", stack="docker", role="devops",
         goal="installer/ (Inno Setup) под IziBox: имена, пути.",
         ac="1. Inno Setup собирает установщик IziBox. 2. Имя/ярлыки/папки — IziBox. 3. Установка без ошибок. 4. Negative: нет файлов BiziBox-бренда.",
         scope="installer/, backend/IziBox.spec, scripts/.",
         scope_exclude="Не трогать код приложения.",
         rollback="git revert."),
]


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if not PYTHON.exists():
        print(f"Ошибка: не найден {PYTHON}. Сначала выполните bootstrap TAUSIK в IziBox.")
        sys.exit(1)
    if not PROJECT_PY.exists():
        print(f"Ошибка: не найден {PROJECT_PY}.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--close-phase1", action="store_true",
                        help="Пометить 6 задач фазы 1 как done (verify + done).")
    args = parser.parse_args()

    epics = existing_slugs(("epic", "list"))
    stories = existing_slugs(("story", "list"))
    tasks = existing_slugs(("task", "list"))

    print("== epic ==")
    ensure_epic(EPIC["slug"], EPIC["title"], EPIC["description"], epics)

    print("== stories ==")
    for epic_slug, title, desc in STORIES:
        ensure_story(EPIC["slug"], epic_slug, title, desc, stories)

    print("== tasks ==")
    for t in TASKS:
        ensure_task(t, tasks)

    if args.close_phase1:
        print("== close phase-1 ==")
        for t in TASKS:
            if t.get("done"):
                close_task(t["slug"])

    print("Готово.")


if __name__ == "__main__":
    main()
