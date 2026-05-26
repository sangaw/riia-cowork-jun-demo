# Role Guardrails — QA

**Scope:** Applies to any agent writing automated tests.  
**Load order:** Load after `org.md`. Load `project.md` alongside this file.  
**Version:** v1 (2026-05-26)

---

## 1. Output Scope

- QA agents write tests only. They do not modify application source code.
- Test destinations: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- If source code is untestable (no dependency injection, global state, hardcoded dependencies), flag it to the user — do not patch source to make tests pass.

## 2. Test Patterns

| Pattern | Rule |
|---|---|
| File-system tests | Use `pytest`'s `tmp_path` fixture — never touch real data directories |
| Environment variables | Use `monkeypatch` to patch `RITA_ENV`, `RITA_JWT_SECRET`, `_CONFIG_DIR`, etc. |
| Module-level imports | Never import `Settings` or singletons at module level — import inside test functions to avoid cross-test side effects |
| Concurrency tests | Use `threading.Barrier` to ensure all threads start simultaneously |
| Integration tests | Use real `CsvRepository` with `tmp_path` — never mock the repository |

## 3. Test Naming

- Test names must describe the scenario being verified: `test_upsert_replaces_existing`, not `test_upsert_2`.
- One assertion focus per test — do not combine multiple unrelated assertions in one test function.

## 4. Coverage Gate

- Coverage must not drop below 80% (`--cov-fail-under=80`).
- New public functions introduced by Engineer agents require at least one corresponding test.
- After writing tests, confirm: `pytest -q --cov=rita --cov-fail-under=80` passes.

## 5. Greeks Tests (core/ protection)

- Before any change to `core/` modules is accepted, QA must run Delta/Gamma/Theta/Vega reference tests against Black-Scholes values.
- If these tests do not exist, QA creates them before anything else.

## 6. API ↔ Frontend Contract Check

- For any new endpoint introduced in the same sprint, QA writes a contract verification test that:
  - Calls the endpoint via the test client
  - Asserts every field the JS consumer reads is present in the response
  - Asserts no field value is `None` where `null` is not a valid sentinel

## 7. Functional Scope

- QA verifies that the feature works end-to-end (functional gate).
- Structural checks (does code match design? are guardrails followed?) are the Reviewer's responsibility, not QA's.
- QA does not re-check reviewer findings — it tests behaviour, not structure.
