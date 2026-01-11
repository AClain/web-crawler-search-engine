import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.engine import BaseModel

if TYPE_CHECKING:
    from .Link import Link


class LinkRelation(BaseModel):
    __tablename__ = "link_relations"
    link_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("links.id"), primary_key=True)
    has_link_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("links.id"), primary_key=True
    )

    # relationships
    parent_link: Mapped["Link"] = relationship(
        "Link",
        foreign_keys=[link_id],
        back_populates="outgoing_relations",
        cascade="all, delete",
    )
    child_link: Mapped["Link"] = relationship(
        "Link",
        foreign_keys=[has_link_id],
        back_populates="incoming_relations",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"LinkRelation(link_id={self.link_id}, has_link_id={self.has_link_id})"
