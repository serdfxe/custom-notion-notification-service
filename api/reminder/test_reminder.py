from datetime import date

import pytest

from fastapi import FastAPI

from starlette.testclient import TestClient
from uuid import UUID, uuid4

from . import reminder_router


app = FastAPI()
app.include_router(reminder_router)


client = TestClient(app)


@pytest.fixture
def user_id():
    return uuid4()


def user_headers(user_id: UUID):
    return {"X-User-Id": str(user_id)}


@pytest.fixture
def reminder_id():
    return uuid4()


@pytest.fixture
def today():
    return date.today()


@pytest.mark.asyncio
async def test_create_reminder(user_id, today):
    response = client.post(
        "/reminder/",
        json={
            "text": "Test Reminder",
            "date": today.isoformat(),
        },
        headers=user_headers(user_id),
    )

    assert response.status_code == 201

    assert "id" in response.json()

    assert "date" in response.json()
    assert response.json()["date"] == today.isoformat()

    assert "text" in response.json()
    assert response.json()["text"] == "Test Reminder"

    assert "user_id" in response.json()
    assert response.json()["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_create_reminder_unauthorized(today):
    response = client.post(
        "/reminder/",
        json={
            "text": "Test Reminder",
            "date": today.isoformat(),
        },
    )

    assert response.status_code == 422

    # assert "detail" in response.json()
    #
    # assert "error_message" in response.json()["detail"]
    # assert response.json()["detail"]["error_message"] == "Missing X-User-Id header."


@pytest.mark.asyncio
async def test_get_reminder(user_id, today):
    response = client.post(
        "/reminder/",
        json={
            "text": "Test Reminder",
            "date": today.isoformat(),
        },
        headers=user_headers(user_id),
    )

    reminder_id = response.json()["id"]

    response = client.get(f"/reminder/{reminder_id}", headers=user_headers(user_id))

    assert response.status_code == 200

    assert "id" in response.json()
    assert response.json()["id"] == reminder_id

    assert "date" in response.json()
    assert response.json()["date"] == today.isoformat()

    assert "text" in response.json()
    assert response.json()["text"] == "Test Reminder"

    assert "user_id" in response.json()
    assert response.json()["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_get_reminder_not_found(user_id, reminder_id):
    response = client.get(f"/reminder/{reminder_id}", headers=user_headers(user_id))
    assert response.status_code == 404

    assert "detail" in response.json()

    assert "error_message" in response.json()["detail"]
    assert response.json()["detail"]["error_message"] == "Reminder not found."


@pytest.fixture
def created_reminder(user_id, today):
    response = client.post(
        "/reminder/",
        json={
            "text": "Test Reminder",
            "date": today.isoformat(),
        },
        headers=user_headers(user_id),
    )

    return response.json()


@pytest.mark.asyncio
async def test_get_reminder_unauthorized(created_reminder):
    reminder_id = created_reminder["id"]

    response = client.get(f"/reminder/{reminder_id}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_reminder_not_found(reminder_id, user_id):
    response = client.get(f"/reminder/{reminder_id}", headers=user_headers(user_id))

    assert response.status_code == 404

    assert "detail" in response.json()

    assert "error_message" in response.json()["detail"]
    assert response.json()["detail"]["error_message"] == "Reminder not found."


@pytest.mark.asyncio
async def test_delete_reminder(created_reminder):
    reminder_id = created_reminder["id"]
    user_id = created_reminder["user_id"]

    response = client.delete(f"/reminder/{reminder_id}", headers=user_headers(user_id))

    assert response.status_code == 200

    response = client.get(f"/reminder/{reminder_id}", headers=user_headers(user_id))

    assert response.status_code == 404

    assert "detail" in response.json()

    assert "error_message" in response.json()["detail"]
    assert response.json()["detail"]["error_message"] == "Reminder not found."


@pytest.mark.asyncio
async def test_delete_reminder_unauthorized(created_reminder):
    reminder_id = created_reminder["id"]
    user_id = created_reminder["user_id"]

    response = client.delete(f"/reminder/{reminder_id}")

    assert response.status_code == 422

    response = client.get(f"/reminder/{reminder_id}", headers=user_headers(user_id))

    assert response.status_code == 200

    assert "id" in response.json()
    assert response.json()["id"] == reminder_id

    assert "date" in response.json()
    assert response.json()["date"] == created_reminder["date"]

    assert "text" in response.json()
    assert response.json()["text"] == created_reminder["text"]

    assert "user_id" in response.json()
    assert response.json()["user_id"] == user_id


def create_reminder(user_id: UUID, date: date):
    response = client.post(
        "/reminder/",
        json={
            "text": "Test Reminder",
            "date": date.isoformat(),
        },
        headers=user_headers(user_id),
    )

    return response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, dates, start_date, end_date, expected_count",
    [
        # Сценарий 1: Нет фильтров, должны вернуть все напоминания
        (uuid4(), [date(2024, 1, 1), date(2024, 1, 15)], None, None, 2),
        # Сценарий 2: Фильтрация по стартовой дате
        (
            uuid4(),
            [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 1)],
            date(2024, 1, 15),
            None,
            2,
        ),
        # Сценарий 3: Фильтрация по конечной дате
        (
            uuid4(),
            [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 1)],
            None,
            date(2024, 1, 15),
            2,
        ),
        # Сценарий 4: Фильтрация по стартовой и конечной дате
        (
            uuid4(),
            [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 1)],
            date(2024, 1, 10),
            date(2024, 1, 20),
            1,
        ),
    ],
)
async def test_get_all_reminders(user_id, dates, start_date, end_date, expected_count):
    for reminder_date in dates:
        create_reminder(user_id, reminder_date)

    params = dict()

    if start_date:
        params["start_date"] = start_date.isoformat()

    if end_date:
        params["end_date"] = end_date.isoformat()

    response = client.get("/reminder/", headers=user_headers(user_id), params=params)

    assert response.status_code == 200

    reminders = response.json()
    assert len(reminders) == expected_count
