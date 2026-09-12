from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import IDMixin, SoftDeleteMixin, TimestampMixin


class Organization(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
    )