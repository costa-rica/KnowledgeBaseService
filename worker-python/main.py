"""Top-level entrypoint for the worker.

Invoked by systemd or directly: python main.py
"""

from src.main import run

if __name__ == "__main__":
    run()
