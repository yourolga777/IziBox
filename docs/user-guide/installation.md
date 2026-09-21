# Установка

## Системные требования

- Windows 10/11 (64-bit)
- 4 ГБ ОЗУ
- 1 ГБ свободного места на диске

## Установка

### Вариант 1: Portable-версия (рекомендуется)

1. Скачайте архив `BiziBox-Portable.zip` со [страницы релизов](https://github.com/anomalyco/BiziBox/releases)
2. Распакуйте архив в любую папку (например, `C:\BiziBox`)
3. Запустите `BiziBox.exe`
4. Откройте браузер и перейдите на `http://localhost:7911`

### Вариант 2: Установка из исходного кода

```bash
git clone https://github.com/anomalyco/BiziBox.git
cd BiziBox

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 7911

# Frontend (отдельный терминал)
cd frontend
npm install
npm run dev
```

## После установки

1. Откройте `http://localhost:7911` в браузере
2. Перейдите в раздел **Каналы** и подключите Telegram или Email
3. Начните получать сообщения в едином инбоксе

## Обновление

Для portable-версии: скачайте новую версию архива и распакуйте поверх существующей папки (ваши данные сохранятся в `data/`).
