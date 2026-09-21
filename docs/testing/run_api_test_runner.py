#!/usr/bin/env python3
"""API test runner для ручного тест-рана Спринта 4 (T-4.0)."""

import asyncio
import httpx
import sys
import json

BASE_URL = "http://localhost:7911"
passed = 0
failed = 0
results = []


def report(tc: str, step: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        results.append(f"  [PASS] {tc} | {step}")
    else:
        failed += 1
        results.append(f"  [FAIL] {tc} | {step} | {detail}")


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        # === TC-1: Health ===
        r = await c.get("/api/health")
        report("TC-1", "Health endpoint", r.status_code == 200 and r.json().get("status") == "ok", str(r.text))
        
        r = await c.get("/docs")
        report("TC-1", "Swagger UI", r.status_code == 200)

        # === TC-2: Contacts ===
        r = await c.get("/api/contacts/")
        report("TC-2", "GET contacts (empty list)", r.status_code == 200, str(r.status_code))

        r = await c.post("/api/contacts/", json={"name": "Иван Петров", "phone": "+79123456789"})
        report("TC-2", "POST contact", r.status_code in (200, 201), str(r.status_code))
        contact_id = r.json().get("id") if r.status_code in (200, 201) else None

        if contact_id:
            r = await c.get(f"/api/contacts/{contact_id}")
            report("TC-2", "GET contact by id", r.status_code == 200, str(r.status_code))

            r = await c.patch(f"/api/contacts/{contact_id}", json={"name": "Иван Сидоров"})
            report("TC-2", "PATCH contact", r.status_code == 200, str(r.status_code))

            r = await c.delete(f"/api/contacts/{contact_id}")
            report("TC-2", "DELETE contact", r.status_code in (200, 204), str(r.status_code))

            r = await c.get(f"/api/contacts/{contact_id}")
            report("TC-2", "GET deleted contact", r.status_code == 404, str(r.status_code))
        else:
            report("TC-2", "Contact CRUD (no id)", False, "contact creation failed")

        r = await c.post("/api/contacts/", json={"name": "", "phone": ""})
        report("TC-2", "POST contact with empty name (validation)", r.status_code == 422, str(r.status_code))

        # === TC-3: Messages ===
        # Create contact first for messages
        r = await c.post("/api/contacts/", json={"name": "Тест Контакт", "phone": "+79999999999"})
        msg_contact_id = r.json().get("id") if r.status_code in (200, 201) else None
        report("TC-3", "Create contact for message tests", msg_contact_id is not None, str(r.status_code))

        if msg_contact_id:
            r = await c.post("/api/messages/", json={
                "contact_id": msg_contact_id, "content": "Здравствуйте!",
                "channel": "telegram", "direction": "incoming"
            })
            report("TC-3", "POST message (incoming)", r.status_code in (200, 201), str(r.status_code))
            msg_id = r.json().get("id") if r.status_code in (200, 201) else None

            r = await c.post("/api/messages/", json={
                "contact_id": msg_contact_id, "content": "Ответ",
                "channel": "telegram", "direction": "outgoing"
            })
            report("TC-3", "POST message (outgoing)", r.status_code in (200, 201), str(r.status_code))

            if msg_id:
                r = await c.get("/api/messages/")
                report("TC-3", "GET messages list", r.status_code == 200, str(r.status_code))

                r = await c.get(f"/api/messages/{msg_id}")
                report("TC-3", "GET message by id", r.status_code == 200, str(r.status_code))

                r = await c.patch(f"/api/messages/{msg_id}", json={"status": "read"})
                report("TC-3", "PATCH message status", r.status_code == 200, str(r.status_code))

                r = await c.get(f"/api/messages/dialog/{msg_contact_id}")
                report("TC-3", "GET dialog", r.status_code == 200, str(r.status_code))

                # POST /messages/bulk not implemented in MVP — skipped

                r = await c.delete(f"/api/messages/{msg_id}")
                report("TC-3", "DELETE message", r.status_code in (200, 204), str(r.status_code))
            else:
                report("TC-3", "Message CRUD (no msg_id)", False, "message creation failed")

            r = await c.post("/api/messages/", json={"contact_id": 99999, "content": "test"})
            report("TC-3", "POST message with invalid contact", r.status_code in (404, 422), str(r.status_code))

            r = await c.post("/api/messages/", json={"contact_id": msg_contact_id, "content": ""})
            report("TC-3", "POST message with empty content", r.status_code == 422, str(r.status_code))

        # === TC-4: Tasks ===
        r = await c.get("/api/tasks/")
        report("TC-4", "GET tasks list", r.status_code == 200, str(r.status_code))

        r = await c.post("/api/tasks/", json={
            "title": "Позвонить клиенту", "description": "Обсудить заказ", "priority": "high"
        })
        report("TC-4", "POST task", r.status_code in (200, 201), str(r.status_code))
        task_id = r.json().get("id") if r.status_code in (200, 201) else None

        if task_id:
            r = await c.get(f"/api/tasks/?status=active")
            report("TC-4", "GET tasks filtered by status", r.status_code == 200, str(r.status_code))

            r = await c.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
            report("TC-4", "PATCH task status", r.status_code == 200, str(r.status_code))

            r = await c.delete(f"/api/tasks/{task_id}")
            report("TC-4", "DELETE task", r.status_code in (200, 204), str(r.status_code))
        else:
            report("TC-4", "Task CRUD (no id)", False, "task creation failed")

        r = await c.post("/api/tasks/", json={"title": ""})
        report("TC-4", "POST task with empty title", r.status_code == 422, str(r.status_code))

        # === TC-5: Dashboard ===
        r = await c.get("/api/dashboard/metrics")
        report("TC-5", "GET dashboard metrics", r.status_code == 200, str(r.status_code))
        if r.status_code == 200:
            data = r.json()
            has_fields = all(k in data for k in ("total_messages", "total_tasks", "total_contacts", "unread_messages"))
            report("TC-5", "Metrics have all fields", has_fields, str(data.keys()))

        r = await c.get("/api/dashboard/funnel")
        report("TC-5", "GET dashboard funnel", r.status_code == 200, str(r.status_code))

        # === TC-6: Channels ===
        r = await c.get("/api/channels/")
        report("TC-6", "GET channels list", r.status_code == 200, str(r.status_code))

        r = await c.post("/api/channels/telegram/connect", json={})
        report("TC-6", "POST telegram connect without phone (validation)", r.status_code == 422, str(r.status_code))

        r = await c.post("/api/channels/email/connect", json={
            "email": "test@test.com", "imap_host": "imap.test.com",
            "imap_port": 993, "smtp_host": "smtp.test.com", "smtp_port": 465,
            "password": "secret"
        })
        # Accept 200 (ok), 201 (created), or 400 (already connected / IMAP unreachable)
        report("TC-6", "POST email connect", r.status_code in (200, 201, 400), str(r.status_code))

        # === TC-8: Error handling ===
        r = await c.get("/api/nonexistent")
        report("TC-8", "GET nonexistent endpoint", r.status_code == 404, str(r.status_code))

        r = await c.patch("/api/contacts/99999", json={"name": "No one"})
        report("TC-8", "PATCH nonexistent contact", r.status_code == 404, str(r.status_code))

        r = await c.delete("/api/contacts/99999")
        report("TC-8", "DELETE nonexistent contact", r.status_code in (404, 204), str(r.status_code))

        r = await c.post("/api/contacts/", data="not json")
        report("TC-8", "POST with invalid JSON", r.status_code == 422, str(r.status_code))

    # === Summary ===
    print(f"\n{'='*50}")
    print(f"API TEST RUNNER RESULTS")
    print(f"{'='*50}")
    for r in results:
        print(r)
    print(f"\n{'='*50}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[TOTAL] Total:  {passed + failed}")
    print(f"{(passed/(passed+failed)*100):.0f}% success rate" if (passed+failed) else "N/A")

    if failed > 0:
        print("\n[WARN] Some tests FAILED. Review failures above.")
        sys.exit(1)
    else:
        print("\n[PASS] All API tests PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run())
