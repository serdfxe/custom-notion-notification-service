from sqlalchemy import Column, Date, String
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base
from core.db.mixins import TimestampMixin


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    user_id = Column(UUID, primary_key=True)

    date = Column(Date, nullable=False)
    text = Column(String, nullable=False, unique=False)
