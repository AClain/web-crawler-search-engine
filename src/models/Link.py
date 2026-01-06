import enum
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Enum, Float, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.engine import BaseModel
from src.models.LinkRelation import LinkRelation


class ChangeFreq(enum.Enum):
    ALWAYS = "always"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"

class Link(BaseModel):
    __tablename__ = "links"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        insert_default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(String(512), unique=True)
    change_freq: Mapped[ChangeFreq] = mapped_column(Enum(ChangeFreq), default=ChangeFreq.MONTHLY)
    priority: Mapped[float] = mapped_column(Float(1), default=0.5)
    lang: Mapped[str | None] = mapped_column(String(3), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    http_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    # relationships
    outgoing_relations: Mapped[list["LinkRelation"]] = relationship(
        foreign_keys="[LinkRelation.link_id]",
        back_populates="parent_link"
    )
    incoming_relations: Mapped[list["LinkRelation"]] = relationship(
        foreign_keys="[LinkRelation.has_link_id]",
        back_populates="child_link"
    )

    def __repr__(self) -> str:
        return f"Link(id={self.id}, url={self.url})"