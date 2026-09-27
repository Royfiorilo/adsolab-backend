# Testing strategy (backend)

How this repo is tested. Each feature's case spec lives in this folder (`<feature>.md`).

## Principles

- **Mostly integration.** Mocks hide boundary bugs: a wrong PostgreSQL `UNIQUE` passed every
  mocked test and broke saving a second version. Anything that depends on the database is tested
  against **real PostgreSQL**.
- **Cases first, tests second.** Each feature gets a spec of identified cases (happy, boundary,
  negative, edge, state) derived with equivalence partitioning, boundary values, decision tables
  and state transitions.
- **A test that cannot fail is useless.** Every new test is checked by breaking the behaviour it
  covers (manual mutation): it must go red.
- **Behaviour, not implementation.** Assert what is observable: return value, HTTP response, rows
  in the database.

## Which level for what

| What | Level | Marker |
|---|---|---|
| Math: models, fitting, linearization, statistics | Unit, synthetic data with known parameters and an explicit tolerance | — |
| Schemas / validation | Unit: every valid and invalid partition + boundaries | — |
| Services touching the DB (save, versions, delete, constraints, cascades, transactions) | **Integration** (real PostgreSQL) | `integration` |
| Controllers (routing, status codes, error mapping) | Flask client, service mocked | — |
| Migrations | CI applies all of them to an empty DB before the tests | — |

Mock the DB only for orchestration with no DB semantics (e.g. "validation runs before the
investigation is created"). Constraints, cascades and transactions are **never** tested with mocks.

## Conventions

- New tests in pytest style. Existing `unittest.TestCase` files stay as they are; don't mix styles in one file.
- Name: `test_should_<result>_when_<condition>`; the case ID goes in the docstring (`"""KSAVE-N03"""`).
- Arrange / Act / Assert separated by blank lines; one behaviour per test.
- Data: builders with valid defaults, overriding only what the test is about (`payload(sample, results=[])`).
- Floats: never `==`; `pytest.approx` / `numpy.testing.assert_allclose` with a stated tolerance.
- Deterministic: no network, no real time, fixed seeds.
- Location: `test/<layer>/<module>_test.py` (unit), `test/integration/<feature>_test.py`.
- Comments short and in English.

## Case types

| Prefix | Meaning |
|---|---|
| `H` | Happy: valid, representative input |
| `B` | Boundary: at / just inside / just outside a limit (min-1, min, min+1, max, max+1) |
| `N` | Negative: invalid input or forbidden action, rejected with the right error |
| `E` | Edge: valid but unusual (zero, allowed empty, duplicates, unsorted, extreme magnitudes) |
| `S` | State / sequence: operation order, idempotency, atomicity |

IDs: `<FEATURE>-<type><nn>`, e.g. `KSAVE-N03`.

## Integration tests

- Need `TEST_DATABASE_URL` pointing to a database named **`*_test`**, built only with `dbmate up`.
  Without it they are **skipped**, not failed; any other database is refused.
- Each test runs in a transaction rolled back at the end (app `commit()`s land on a SAVEPOINT).
- Fixtures (`test/integration/conftest.py`): `db_session`, `make_user`, `make_kinetic_sample`.
- `db.session` is swapped for a SQLAlchemy `scoped_session` bound to the test connection:
  Flask-SQLAlchemy 3.1 ignores the session bind, so `db.session.configure(bind=...)` leaks rows
  past the rollback (verified).

## Coverage

Line coverage via `pytest-cov`, published as a badge by CI. A signal, not a target: no minimum
threshold.

## Not adopted

- **`pytest-flask-sqlalchemy`:** unmaintained, built for SQLAlchemy 1.x (we use 2.0).
- **testcontainers:** redundant with docker compose (local) and the service container (CI).
- **Coverage threshold, mutation tools (mutmut):** not worth it at this size; the manual check per
  test covers the intent.
