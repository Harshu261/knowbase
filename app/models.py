from sqlalchemy import String,DateTime,Text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text,nullable=False)
    subject: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=True
    )
    file_path : Mapped[str | None] = mapped_column(Text,nullable=True)
    content: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
    )
