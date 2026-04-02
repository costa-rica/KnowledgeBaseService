"""Embedding generator — creates and upserts vector embeddings for markdown files."""

import uuid
from pathlib import Path

from loguru import logger
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from db_models.models.markdown_file_embeddings import (
    EMBEDDING_DIMENSIONS,
    MarkdownFileEmbedding,
)
from db_models.models.markdown_files import MarkdownFile

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SNIPPET_LENGTH = 500

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: {}", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _read_file_content(vault_path: str, relative_path: str) -> str | None:
    """Read the full content of a markdown file.

    Returns:
        File content as a string, or None if the file can't be read.
    """
    full_path = Path(vault_path) / relative_path
    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read {}: {}", full_path, exc)
        return None


def generate_embeddings(
    session: Session,
    vault_path: str,
    new_files: list[MarkdownFile],
    modified_files: list[MarkdownFile],
) -> dict:
    """Generate and upsert embeddings for new and modified files.

    For new files, inserts a row into markdown_file_embeddings.
    For modified files, updates the existing embedding row.

    Args:
        session: An open SQLAlchemy session.
        vault_path: Absolute path to the vault root.
        new_files: MarkdownFile records for newly discovered files.
        modified_files: MarkdownFile records for files with updated mtime.

    Returns:
        A dict with counts: {"embedded": int, "errors": int}.
    """
    model = _get_model()
    counts = {"embedded": 0, "errors": 0}

    # Process new files — insert embeddings.
    for record in new_files:
        content = _read_file_content(vault_path, record.file_path)
        if content is None:
            counts["errors"] += 1
            continue

        try:
            vector = model.encode(content).tolist()
            snippet = content[:SNIPPET_LENGTH]

            embedding = MarkdownFileEmbedding(
                id=uuid.uuid4(),
                markdown_file_id=record.id,
                embedding=vector,
                snippet=snippet,
            )
            session.add(embedding)
            counts["embedded"] += 1
        except Exception as exc:
            logger.error(
                "Failed to generate embedding for {}: {}",
                record.file_path,
                exc,
            )
            counts["errors"] += 1

    # Process modified files — update existing embeddings.
    for record in modified_files:
        content = _read_file_content(vault_path, record.file_path)
        if content is None:
            counts["errors"] += 1
            continue

        try:
            vector = model.encode(content).tolist()
            snippet = content[:SNIPPET_LENGTH]

            existing = (
                session.query(MarkdownFileEmbedding)
                .filter_by(markdown_file_id=record.id)
                .first()
            )

            if existing:
                existing.embedding = vector
                existing.snippet = snippet
            else:
                # Edge case: file record exists but embedding is missing.
                embedding = MarkdownFileEmbedding(
                    id=uuid.uuid4(),
                    markdown_file_id=record.id,
                    embedding=vector,
                    snippet=snippet,
                )
                session.add(embedding)

            counts["embedded"] += 1
        except Exception as exc:
            logger.error(
                "Failed to update embedding for {}: {}",
                record.file_path,
                exc,
            )
            counts["errors"] += 1

    session.flush()

    logger.info(
        "Embedding generation complete: {} embedded, {} errors",
        counts["embedded"],
        counts["errors"],
    )

    return counts
