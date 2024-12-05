from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Depends, HTTPException

from core.db.repository import DatabaseRepository
from core.fastapi.dependencies import get_repository

from app.models.reminder import Reminder

from .dto import ReminderResponseDTO, ReminderCreateDTO


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
    repository: ReminderRepository,
):
    """
    Retrieve reminder data.

    This operation fetches the details of a specific reminder associated with
    the provided `reminder_id` and the user identification, which is obtained
    from the X-User-Id header. If no reminder is found for the specified ID,
    a 404 error will be returned.
    """

    reminder = await repository.get(
        Reminder.id == reminder_id, Reminder.user_id == x_user_id
    )

    if not reminder:
        raise HTTPException(
            status_code=404, detail={"error_message": "Reminder not found."}
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
    repository: ReminderRepository,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Retrieve all reminder data.

    This endpoint allows you to access all reminders associated with a specific user,
    whose identification is provided by the X-User-Id header.

    Date filtering parameters:
    - If only the `start_date` parameter is set, all reminders that start after the specified date
      (inclusive) will be returned.
    - If both parameters (`start_date` and `end_date`) are provided, all reminders occurring
      within the range defined by these two dates (inclusive) will be returned.
    - If only the `end_date` parameter is set, all reminders occurring before the specified
      date (inclusive) will be returned.
    - If neither parameter is set, all reminders associated with the user will be returned.

    The returned data is presented in the ReminderResponseDTO format.
    """
    filters = [Reminder.user_id == x_user_id]

    if start_date:
        filters.append(Reminder.date >= start_date)
    if end_date:
        filters.append(Reminder.date <= end_date)

    reminders = await repository.filter(*filters)
    return reminders


@reminder_router.post(
    "/",
    status_code=201,
    response_model=ReminderResponseDTO,
    responses={
        201: {"description": "Reminder created successfully."},
    },
)
async def create_reminder_route(
    data: ReminderCreateDTO,
    x_user_id: Annotated[str, Header()],
    repository: ReminderRepository,
):
    """
    Create a new reminder.

    This operation allows the creation of a new reminder based on the provided
    data. The reminder is linked to the user identified by the X-User-Id header.
    If the input data is invalid or if a reminder with the same details already
    exists, appropriate error responses will be returned (400 for bad requests
    and 409 for conflicts).
    """

    existing_reminder = await repository.filter(
        Reminder.user_id == x_user_id,
        Reminder.text == data.text,
        Reminder.date == data.date,
    )

    if existing_reminder:
        raise HTTPException(
            status_code=409, detail={"error_message": "Reminder already exists."}
        )

    new_reminder = await repository.create(
        user_id=x_user_id, text=data.text, date=data.date
    )

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
    repository: ReminderRepository,
):
    """
    Delete a reminder.

    This operation removes the reminder associated with the specified `id`
    and the user identification, which is verified through the X-User-Id header.
    If the reminder does not exist, a 404 error will be returned.
    """

    try:
        await repository.get(Reminder.id == reminder_id, Reminder.user_id == x_user_id)
    except Exception:
        raise HTTPException(
            status_code=404, detail={"error_message": "Reminder not found."}
        )

    await repository.delete(Reminder.id == reminder_id, Reminder.user_id == x_user_id)
