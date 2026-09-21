import pytest

from app.database import init_db
from tests.conftest import make_client


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db(clear_first=True)


async def _make_contact(client, name: str, **extra) -> int:
    resp = await client.post("/api/contacts/", json={"name": name, **extra})
    assert resp.status_code == 201
    return int(resp.json()["id"])


@pytest.mark.asyncio
async def test_contact_crud_supports_all_four_types():
    async with make_client() as client:
        for contact_type in ("personal", "needed", "spam", "other"):
            resp = await client.post(
                "/api/contacts/",
                json={"name": f"Type {contact_type}", "contact_type": contact_type},
            )
            assert resp.status_code == 201
            assert resp.json()["contact_type"] == contact_type

            cid = resp.json()["id"]
            detail = await client.get(f"/api/contacts/{cid}")
            assert detail.json()["contact_type"] == contact_type


@pytest.mark.asyncio
async def test_contact_type_defaults_to_other():
    async with make_client() as client:
        resp = await client.post("/api/contacts/", json={"name": "Без типа"})
    assert resp.status_code == 201
    assert resp.json()["contact_type"] == "other"


@pytest.mark.asyncio
async def test_contact_type_employee_rejected_422():
    async with make_client() as client:
        created = await client.post(
            "/api/contacts/", json={"name": "Employee", "contact_type": "employee"}
        )
    assert created.status_code == 422


@pytest.mark.asyncio
async def test_contact_create_with_nonexistent_folder_returns_400():
    async with make_client() as client:
        resp = await client.post(
            "/api/contacts/", json={"name": "Bad Folder", "folder_id": 999999}
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_contact_update_with_nonexistent_folder_returns_400():
    async with make_client() as client:
        cid = await _make_contact(client, "Contact")
        resp = await client.patch(
            f"/api/contacts/{cid}", json={"folder_id": 999999}
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_contact_update_with_existing_folder_succeeds():
    async with make_client() as client:
        folder = await client.post("/api/folders/", json={"name": "VIP"})
        fid = folder.json()["id"]
        cid = await _make_contact(client, "Contact")

        resp = await client.patch(f"/api/contacts/{cid}", json={"folder_id": fid})
    assert resp.status_code == 200
    assert resp.json()["folder_id"] == fid


@pytest.mark.asyncio
async def test_bulk_update_contact_type():
    async with make_client() as client:
        cid = await _make_contact(client, "Contact")
        resp = await client.patch(
            "/api/contacts/bulk-update",
            json={"ids": [cid], "contact_type": "needed"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

        detail = await client.get(f"/api/contacts/{cid}")
    assert detail.json()["contact_type"] == "needed"
