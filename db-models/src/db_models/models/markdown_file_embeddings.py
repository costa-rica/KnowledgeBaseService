import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base

EMBEDDING_DIMENSIONS = 384


class MarkdownFileEmbedding(Base):
    __tablename__ = "markdown_file_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    markdown_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("markdown_files.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[Vector] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=False
    )
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    markdown_file: Mapped["MarkdownFile"] = relationship(
        "MarkdownFile", back_populates="embeddings"
    )
