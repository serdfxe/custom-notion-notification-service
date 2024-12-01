from datetime import date
from time import strptime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Header, Request, Depends, Response, status

from core.db.repository import DatabaseRepository
from core.fastapi.dependencies import get_repository

from app.models.reminder import Reminder

from .dto import GetRemindersByDateDTO, ReminderResponseDTO, ReminderCreateDTO


ReminderRepository = Annotated[
    DatabaseRepository[Reminder],
    Depends(get_repository(Reminder)),
]

reminder_router = APIRouter(prefix="/reminder", tags=["reminder"])


@reminder_router.get(
    "/{reminder_id}",
    response_model=ReminderResponseDTO,
    responses={
        200: {"description": "Reminder data retrieved successfully."},
        404: {"description": "Reminder not found."},
    },
)
async def get_reminder_route(
    reminder_id: UUID,
    x_user_id: Annotated[str, Header()],
    request: Request,
    repository: ReminderRepository,
):
    user_id = x_user_id
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_message": "Missing X-User-Id header."},
        )

    reminder = await repository.get(
        Reminder.id == reminder_id, Reminder.user_id == user_id
    )
    if reminder is None or reminder.user_id != UUID(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_message": "Reminder not found."},
        )

    return reminder


@reminder_router.get(
    "/",
    response_model=list[ReminderResponseDTO],
    responses={
        200: {"description": "Reminder data retrieved successfully."},
    },
)
async def get_all_reminders_route(
    x_user_id: Annotated[str, Header()],
    request: Request,
    repository: ReminderRepository,
    start_date: date | None = None,
    end_date: date | None = None,
):
    user_id = x_user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_message": "Missing X-User-Id header."},
        )

    if start_date is None:
        if end_date is None:
            reminders = await repository.filter(
                Reminder.user_id == user_id,
            )
        else:
            reminders = await repository.filter(
                Reminder.user_id == user_id,
                Reminder.date <= end_date,
            )
    else:
        if end_date is None:
            reminders = await repository.filter(
                Reminder.user_id == user_id,
                Reminder.date >= start_date,
            )
        else:
            reminders = await repository.filter(
                Reminder.user_id == user_id,
                Reminder.date >= start_date,
                Reminder.date <= end_date,
            )

    return reminders


@reminder_router.post(
    "/",
    response_model=ReminderResponseDTO,
    responses={
        201: {"description": "Reminder created successfully."},
    },
)
async def create_reminder_route(
    data: ReminderCreateDTO,
    request: Request,
    response: Response,
    repository: ReminderRepository,
):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_message": "Missing X-User-Id header."},
        )

    new_reminder = await repository.create(
        id=uuid4(),
        user_id=UUID(user_id),
        date=data.date,
        text=data.text,
    )

    response.status_code = status.HTTP_201_CREATED

    return new_reminder


@reminder_router.delete(
    "/{reminder_id}",
    responses={
        200: {"description": "Reminder deleted successfully."},
        404: {"description": "Reminder not found."},
    },
)
async def delete_reminder_route(
    reminder_id: UUID,
    x_user_id: Annotated[str, Header()],
    request: Request,
    repository: ReminderRepository,
):
    user_id = x_user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_message": "Missing X-User-Id header."},
        )

    reminder_to_delete = await repository.get(Reminder.id == reminder_id)
    if reminder_to_delete is None or reminder_to_delete.user_id != UUID(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_message": "Reminder not found."},
        )

    await repository.delete(Reminder.id == reminder_id)
