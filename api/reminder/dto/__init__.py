from datetime import date
from uuid import UUID
from pydantic import BaseModel


class ReminderBase(BaseModel):
    text: str
    date: date

    class Config:
        from_attributes = True


class ReminderCreateDTO(ReminderBase): ...


class ReminderResponseDTO(ReminderBase):
    id: UUID
    user_id: UUID


class GetRemindersByDateDTO(BaseModel):
    start_date: date | None
    end_date: date | None
