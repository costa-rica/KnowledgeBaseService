"""Generate a new API token and insert its hash into the api_keys table."""

import argparse
import secrets
import sys

from db_models import ApiKey, get_engine, get_session_factory
from src.auth import hash_token


def generate_token(name: str) -> str:
    token = secrets.token_urlsafe(32)

    engine = get_engine()
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        api_key = ApiKey(key_hash=hash_token(token), name=name)
        session.add(api_key)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return token


def main():
    parser = argparse.ArgumentParser(description="Generate a new API token")
    parser.add_argument("--name", required=True, help="Human-readable label for the key")
    args = parser.parse_args()

    token = generate_token(args.name)
    print(token)


if __name__ == "__main__":
    main()
