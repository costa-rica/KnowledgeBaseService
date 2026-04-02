import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from db_models import ApiKey, get_engine, get_session_factory

_session_factory = None
_security = HTTPBearer()


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_db() -> Session:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: Session = Depends(get_db),
) -> ApiKey:
    token_hash = hash_token(credentials.credentials)
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == token_hash).first()
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
