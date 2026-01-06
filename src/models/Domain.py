import uuid
from datetime import datetime

from sqlalchemy import UUID, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.engine import BaseModel


class Domain(BaseModel):
    __tablename__ = "domains"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        insert_default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True)
    protocol: Mapped[str] = mapped_column(String(10))
    crawl_delay: Mapped[int] = mapped_column(SmallInteger, default=5)
    has_robots_txt: Mapped[bool | None] = mapped_column(nullable=True)
    is_blocked: Mapped[bool | None] = mapped_column(nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    first_discovered_at: Mapped[datetime] = mapped_column(
        default=datetime.now()
    )

    def __repr__(self) -> str:
        return f"Domain(id={self.id}, name={self.name})"