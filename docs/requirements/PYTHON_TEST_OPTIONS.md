# Python Test Options

## 1. What do we call the worker-python test method?

The best umbrella term is automated tests. "Unit tests" is more specific: those tests isolate a small function, class, or module and usually avoid real network, database, or process boundaries. In `worker-python`, the current setup is broader than unit testing because it includes `unit`, `integration`, and `contract` markers under one `pytest` suite. So if we are naming the overall approach, "automated Python tests with pytest" is the most accurate short label. If we are naming one slice of it, then "unit tests" is correct only for the tests under `tests/unit`. This distinction matters because it sets the right expectation for speed, isolation, and server safety.

## 2. Conventional Python testing options, including the current worker-python automated test method

### `pytest` automated test suite

1. This is the current `worker-python` method.
2. `make test` runs `python -m pytest --cov=src --cov-report=term-missing`.
3. The suite mixes `unit`, `integration`, and `contract` tests.
4. Good fit when we want one practical test command with useful coverage.
5. Ubuntu server fit: very good for dev servers; okay on production for controlled read-only checks, but full runs are usually better in CI or maintenance windows.
6. API endpoint fit: very good. `pytest` works well for endpoint, request/response, and workflow testing.
7. Python cron service fit: very good. It works well for job logic, scheduling helpers, and service modules.

### `unittest` from the Python standard library

1. This is the most lightweight conventional Python test framework because it needs no third-party runner.
2. Best for small isolated tests and basic CI checks.
3. Ubuntu server fit: very good for dev servers; usually safe on production only for small read-only checks that do not touch shared state.
4. API endpoint fit: fair. It can test APIs, but it is usually less pleasant than `pytest` for fixtures and test readability.
5. Python cron service fit: very good. It is simple and solid for service functions, helpers, and scheduled job logic.

### Smoke tests with `curl` or a small shell script

1. This is lighter than a full test suite and focuses on whether the service starts and key endpoints respond.
2. Best for deploy verification, health checks, and quick post-release confidence.
3. Ubuntu server fit: very good for both dev and production, as long as production checks stay read-only and narrow.
4. API endpoint fit: very good for basic endpoint verification, but weak for deeper business logic coverage.
5. Python cron service fit: fair. It can confirm a cron-triggered script runs, but it is not great for detailed internal logic testing.
