import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session

from db_models import MarkdownFile, MarkdownFileEmbedding
from src.auth import get_db, verify_token

router = APIRouter(prefix="/obsidian", tags=["obsidian"])

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


class MatchRequest(BaseModel):
    question: str


class MatchResult(BaseModel):
    id: uuid.UUID
    file_name: str
    file_path: str
    score: float
    snippet: str


class MatchResponse(BaseModel):
    matches: list[MatchResult]


@router.post("/matches", response_model=MatchResponse)
def find_matches(
    body: MatchRequest,
    api_key=Depends(verify_token),
    db: Session = Depends(get_db),
):
    model = _get_model()
    embedding = model.encode(body.question).tolist()

    results = db.execute(
        text("""
            SELECT
                e.id,
                f.file_name,
                f.file_path,
                1 - (e.embedding <=> :embedding::vector) AS score,
                e.snippet
            FROM markdown_file_embeddings e
            JOIN markdown_files f ON f.id = e.markdown_file_id
            ORDER BY e.embedding <=> :embedding::vector
            LIMIT 5
        """),
        {"embedding": str(embedding)},
    ).fetchall()

    return MatchResponse(
        matches=[
            MatchResult(
                id=row.id,
                file_name=row.file_name,
                file_path=row.file_path,
                score=round(float(row.score), 4),
                snippet=row.snippet,
            )
            for row in results
        ]
    )


class FileResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    file_path: str
    content: str


@router.get("/file/{file_id}", response_model=FileResponse)
def get_file(
    file_id: uuid.UUID,
    api_key=Depends(verify_token),
    db: Session = Depends(get_db),
):
    record = db.query(MarkdownFile).filter(MarkdownFile.id == file_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(record.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found on disk")

    content = file_path.read_text(encoding="utf-8")

    return FileResponse(
        id=record.id,
        file_name=record.file_name,
        file_path=record.file_path,
        content=content,
    )
