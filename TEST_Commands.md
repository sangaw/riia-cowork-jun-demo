Run from the workspace root (riia-cowork-jun/). If Playwright browsers aren't installed yet: playwright install
chromium.


cd riia-jun-release

# Unit tests
pytest tests/unit/ --junitxml=test-results/unit/latest.xml -v

# Integration tests
pytest tests/integration/ --junitxml=test-results/integration/latest.xml -v


# End-to-end tests (requires Playwright browsers installed)
pytest tests/e2e/ --junitxml=test-results/e2e/ -v

pytest tests/e2e/test_rita_scenarios.py --junitxml="test-results/e2e/rita/latest.xml" -v
pytest tests/e2e/test_fno_scenarios.py --junitxml="test-results/e2e/fno/latest.xml" -v
pytest tests/e2e/test_ops_scenarios.py --junitxml="test-results/e2e/ops/latest.xml" -v


# All tests with coverage report
pytest tests/ -v --cov=riia-jun-release/src/rita --cov-report=term-missing
