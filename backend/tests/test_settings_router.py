import json
from unittest.mock import patch

import pytest

from app.config import settings as app_settings
from tests.conftest import make_client


def _onboarding_file(tmp_path):
    return tmp_path / "onboarding.enc"


def _write_onboarding(payload: dict[str, object], monkeypatch, tmp_path):
    enc_file = _onboarding_file(tmp_path)
    from app.utils.crypto import encrypt
    enc_file.write_text(encrypt(json.dumps(payload)), encoding="utf-8")
    monkeypatch.setattr("app.routers.settings.get_user_onboarding_file", lambda _login: enc_file)
    return enc_file


@pytest.mark.asyncio
async def test_onboarding_config_empty_when_no_file(tmp_path, monkeypatch):
    enc_file = _onboarding_file(tmp_path)
    monkeypatch.setattr("app.routers.settings.get_user_onboarding_file", lambda _login: enc_file)
    monkeypatch.setattr(app_settings, "TELEGRAM_API_HASH", "0123456789abcdef0123456789abcdef")
    async with make_client() as client:
        response = await client.get("/api/settings/onboarding-config")
    assert response.status_code == 200
    data = response.json()
    body = json.dumps(data)
    assert "0123456789abcdef0123456789abcdef" not in body
    assert "35292436c9eaf4972b461d783dedfd09" not in body


@pytest.mark.asyncio
async def test_onboarding_config_returns_secrets_but_hides_api(tmp_path, monkeypatch):
    _write_onboarding(
        {
            "telegram": {
                "api_id": 123456,
                "api_hash": "0123456789abcdef0123456789abcdef",
                "phone": "+79991234567",
                "password_2fa": "my2fapass",
            },
            "email": {"email": "a@b.c", "password": "supersecretpassword"},
            "proxy": {
                "type": "socks5", "host": "127.0.0.1", "port": 1080,
                "username": "u", "password": "p", "secret": "s",
            },
        },
        monkeypatch,
        tmp_path,
    )
    async with make_client() as client:
        response = await client.get("/api/settings/onboarding-config")
    assert response.status_code == 200
    data = response.json()
    # Локальные секреты возвращаются для предзаполнения
    assert data["telegram"]["password_2fa"] == "my2fapass"
    assert data["email"]["password"] == "supersecretpassword"
    # API id/hash не отдаём
    assert "api_id" not in data["telegram"]
    assert "api_hash" not in data["telegram"]
    assert "api_hash_set" not in data["telegram"]
    # Прокси-секреты маскируем
    assert data["proxy"]["password"] != "p"
    assert data["proxy"]["secret"] != "s"


@pytest.mark.asyncio
async def test_onboarding_config_does_not_inject_proxy_credentials_from_env(tmp_path, monkeypatch):
    _write_onboarding({}, monkeypatch, tmp_path)
    with patch.object(
        app_settings,
        "TELEGRAM_PROXY_ENABLED",
        True,
    ), patch.object(app_settings, "TELEGRAM_PROXY_HOST", "proxy.local"):
        async with make_client() as client:
            response = await client.get("/api/settings/onboarding-config")
    assert response.status_code == 200
    data = response.json()
    assert "password" not in data.get("proxy", {})
    assert "secret" not in data.get("proxy", {})


@pytest.mark.asyncio
async def test_onboarding_config_does_not_return_api_id_hash(tmp_path, monkeypatch):
    _write_onboarding({}, monkeypatch, tmp_path)
    with patch.object(app_settings, "TELEGRAM_API_ID", 999), patch.object(
        app_settings, "TELEGRAM_API_HASH", "abcde12345fghij67890klmno"
    ):
        async with make_client() as client:
            response = await client.get("/api/settings/onboarding-config")
    assert response.status_code == 200
    data = response.json()
    assert "api_id" not in data.get("telegram", {})
    assert "api_hash" not in data.get("telegram", {})
    assert "api_hash_set" not in data.get("telegram", {})


@pytest.mark.asyncio
async def test_onboarding_config_corrupt_file_logs_and_returns_empty(tmp_path, monkeypatch, caplog):
    enc_file = _onboarding_file(tmp_path)
    enc_file.write_text("not-a-valid-ciphertext", encoding="utf-8")
    monkeypatch.setattr("app.routers.settings.get_user_onboarding_file", lambda _login: enc_file)
    import logging
    with caplog.at_level(logging.ERROR, logger="app.routers.settings"):
        async with make_client() as client:
            response = await client.get("/api/settings/onboarding-config")
    assert response.status_code == 200
    assert any("ONBOARDING_FILE" in r.message for r in caplog.records)
