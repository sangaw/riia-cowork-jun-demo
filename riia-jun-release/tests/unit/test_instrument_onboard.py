"""Unit tests for instrument onboard endpoints — Feature 09 Run A.

Tests cover:
  GET  /api/v1/instrument/search   — happy path, q too short (400), yfinance unreachable (502)
  POST /api/v1/instrument/onboard  — happy path, duplicate ticker (409),
                                     fewer than 100 rows (400), yfinance unreachable (502)

Strategy
--------
- yfinance calls are mocked via unittest.mock.patch so no network traffic is made.
- DB dependency (get_db) is overridden via FastAPI dependency_overrides with an
  in-memory SQLite session (same pattern as conftest.py / test_api_workflow.py).
- InstrumentRepository.find_by_id is patched to control duplicate-check behaviour.
- fetch_raw_data / process_to_input / seed_market_cache are patched at the service
  module level for the onboard POST pipeline tests so file I/O is avoided.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_VALID_ONBOARD_PAYLOAD = {
    "ticker": "RELIANCE.NS",
    "name": "Reliance Industries Ltd",
    "exchange": "NSI",
    "currency": "INR",
    "country_code": "IN",
    "lot_size": 250,
}

_MOCK_SEARCH_RESULTS = [
    {
        "symbol":    "RELIANCE.NS",
        "longname":  "Reliance Industries Limited",
        "exchange":  "NSI",
        "currency":  "INR",
        "country":   "India",
        "quoteType": "EQUITY",
    },
    {
        "symbol":    "TCS.NS",
        "longname":  "Tata Consultancy Services Limited",
        "exchange":  "NSI",
        "currency":  "INR",
        "country":   "India",
        "quoteType": "EQUITY",
    },
]

# Expected fields the frontend (Run B) reads from each endpoint
_SEARCH_FRONTEND_FIELDS = {"ticker", "name", "exchange", "currency", "country", "quote_type"}
_ONBOARD_FRONTEND_FIELDS = {"status", "ticker", "rows_fetched", "rows_seeded", "raw_path", "input_path"}


# ---------------------------------------------------------------------------
# Helper — build a TestClient with get_db overridden using an in-memory session
# ---------------------------------------------------------------------------

def _make_client():
    """Return (app, TestClient) with get_db wired to an in-memory SQLite session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from rita.database import Base, get_db
    from rita.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    return app, client, session, engine


def _cleanup(app, session, engine):
    from rita.database import Base, get_db
    app.dependency_overrides.pop(get_db, None)
    session.close()
    from rita.database import Base
    Base.metadata.drop_all(engine)
    engine.dispose()


# ===========================================================================
# GET /api/v1/instrument/search
# ===========================================================================

class TestInstrumentSearch:

    def test_search_happy_path_returns_200_and_list(self):
        """GET /api/v1/instrument/search?q=reliance returns 200 and a list of equities."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.services.instrument_onboard.yf",
                create=True,
            ):
                with patch(
                    "rita.services.instrument_onboard.search_tickers",
                    return_value=[
                        {
                            "ticker":     "RELIANCE.NS",
                            "name":       "Reliance Industries Limited",
                            "exchange":   "NSI",
                            "currency":   "INR",
                            "country":    "India",
                            "quote_type": "EQUITY",
                        }
                    ],
                ):
                    response = client.get("/api/v1/instrument/search?q=reliance")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
        finally:
            _cleanup(app, session, engine)

    def test_search_happy_path_response_fields_match_frontend_contract(self):
        """Search response dict contains exactly the fields expected by the frontend."""
        app, client, session, engine = _make_client()
        try:
            # The router uses a 'from' import so we must patch in the router's namespace
            with patch(
                "rita.api.v1.workflow.instrument_onboard.search_tickers",
                return_value=[
                    {
                        "ticker":     "RELIANCE.NS",
                        "name":       "Reliance Industries Limited",
                        "exchange":   "NSI",
                        "currency":   "INR",
                        "country":    "India",
                        "quote_type": "EQUITY",
                    }
                ],
            ):
                response = client.get("/api/v1/instrument/search?q=reliance")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            # All frontend-required fields must be present
            for field in _SEARCH_FRONTEND_FIELDS:
                assert field in data[0], f"Missing field: {field}"
        finally:
            _cleanup(app, session, engine)

    def test_search_quote_type_is_always_equity(self):
        """search_tickers() only returns EQUITY results; quote_type field is 'EQUITY'."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.services.instrument_onboard.search_tickers",
                return_value=[
                    {
                        "ticker":     "TCS.NS",
                        "name":       "Tata Consultancy Services",
                        "exchange":   "NSI",
                        "currency":   "INR",
                        "country":    "India",
                        "quote_type": "EQUITY",
                    }
                ],
            ):
                response = client.get("/api/v1/instrument/search?q=tcs")

            assert response.status_code == 200
            assert response.json()[0]["quote_type"] == "EQUITY"
        finally:
            _cleanup(app, session, engine)

    def test_search_returns_empty_list_when_no_matches(self):
        """GET /api/v1/instrument/search returns 200 with empty list if no equities found."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.services.instrument_onboard.search_tickers",
                return_value=[],
            ):
                response = client.get("/api/v1/instrument/search?q=zzznomatch")

            assert response.status_code == 200
            assert response.json() == []
        finally:
            _cleanup(app, session, engine)

    def test_search_q_too_short_returns_400(self):
        """GET /api/v1/instrument/search?q=x returns 400 — q must be >= 2 chars."""
        app, client, session, engine = _make_client()
        try:
            response = client.get("/api/v1/instrument/search?q=x")
            assert response.status_code == 400
            assert "2 characters" in response.json().get("detail", "").lower() or \
                   "q" in response.json().get("detail", "").lower()
        finally:
            _cleanup(app, session, engine)

    def test_search_q_whitespace_only_returns_400(self):
        """GET /api/v1/instrument/search?q=%20 (single space) returns 400 after strip."""
        app, client, session, engine = _make_client()
        try:
            response = client.get("/api/v1/instrument/search?q= ")
            assert response.status_code == 400
        finally:
            _cleanup(app, session, engine)

    def test_search_yfinance_unreachable_returns_502(self):
        """GET /api/v1/instrument/search returns 502 when yfinance raises ConnectionError."""
        from fastapi import HTTPException

        app, client, session, engine = _make_client()
        try:
            # The router uses `from rita.services.instrument_onboard import search_tickers`
            # so we must patch in the router's own namespace, not the service module.
            with patch(
                "rita.api.v1.workflow.instrument_onboard.search_tickers",
                side_effect=HTTPException(status_code=502, detail="Yahoo Finance is currently unreachable."),
            ):
                response = client.get("/api/v1/instrument/search?q=reliance")

            assert response.status_code == 502
            assert "unreachable" in response.json().get("detail", "").lower()
        finally:
            _cleanup(app, session, engine)

    def test_search_yfinance_timeout_returns_502(self):
        """GET /api/v1/instrument/search returns 502 on TimeoutError from yfinance."""
        from fastapi import HTTPException

        app, client, session, engine = _make_client()
        try:
            # Patch at router namespace — same reason as above.
            with patch(
                "rita.api.v1.workflow.instrument_onboard.search_tickers",
                side_effect=HTTPException(status_code=502, detail="Yahoo Finance is currently unreachable."),
            ):
                response = client.get("/api/v1/instrument/search?q=infosys")

            assert response.status_code == 502
        finally:
            _cleanup(app, session, engine)


# ===========================================================================
# POST /api/v1/instrument/onboard
# ===========================================================================

class TestInstrumentOnboard:

    def test_onboard_happy_path_returns_200(self):
        """POST /api/v1/instrument/onboard returns 200 and full pipeline response."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None  # not a duplicate
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            assert response.status_code == 200
        finally:
            _cleanup(app, session, engine)

    def test_onboard_happy_path_response_fields_match_frontend_contract(self):
        """POST /api/v1/instrument/onboard returns all frontend-required fields."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            assert response.status_code == 200
            data = response.json()
            for field in _ONBOARD_FRONTEND_FIELDS:
                assert field in data, f"Missing response field: {field}"
        finally:
            _cleanup(app, session, engine)

    def test_onboard_happy_path_status_is_ok(self):
        """POST /api/v1/instrument/onboard response body has status='ok'."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            assert response.json()["status"] == "ok"
        finally:
            _cleanup(app, session, engine)

    def test_onboard_ticker_is_uppercased_in_response(self):
        """POST /api/v1/instrument/onboard returns ticker in upper-case."""
        app, client, session, engine = _make_client()
        payload = {**_VALID_ONBOARD_PAYLOAD, "ticker": "reliance.ns"}
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=payload)

            assert response.status_code == 200
            assert response.json()["ticker"] == "RELIANCE.NS"
        finally:
            _cleanup(app, session, engine)

    def test_onboard_rows_fetched_and_seeded_are_numeric(self):
        """POST /api/v1/instrument/onboard returns integer rows_fetched and rows_seeded."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            data = response.json()
            assert isinstance(data["rows_fetched"], int)
            assert isinstance(data["rows_seeded"], int)
            assert data["rows_fetched"] == 3800
            assert data["rows_seeded"] == 120
        finally:
            _cleanup(app, session, engine)

    def test_onboard_duplicate_ticker_returns_409(self):
        """POST /api/v1/instrument/onboard returns 409 when ticker already exists in DB."""
        from rita.schemas.instrument import Instrument
        from datetime import datetime, timezone

        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo:
                # Simulate existing instrument record
                existing_instrument = Instrument(
                    instrument_id="RELIANCE.NS",
                    name="Reliance Industries Ltd",
                    exchange="NSI",
                    country_code="IN",
                    currency="INR",
                    lot_size=250,
                    is_available=True,
                    created_at=datetime.now(timezone.utc),
                )
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = existing_instrument
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            assert response.status_code == 409
            assert "already exists" in response.json().get("detail", "").lower()
        finally:
            _cleanup(app, session, engine)

    def test_onboard_fewer_than_100_rows_returns_400(self):
        """POST /api/v1/instrument/onboard returns 400 when yfinance returns < 100 rows."""
        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                side_effect=ValueError("Ticker 'BADTICKER' returned fewer than 100 rows from Yahoo Finance (got 5). Verify the ticker symbol is correct."),
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                payload = {**_VALID_ONBOARD_PAYLOAD, "ticker": "BADTICKER"}
                response = client.post("/api/v1/instrument/onboard", json=payload)

            assert response.status_code == 400
            assert "100" in response.json().get("detail", "") or \
                   "fewer" in response.json().get("detail", "").lower()
        finally:
            _cleanup(app, session, engine)

    def test_onboard_yfinance_unreachable_returns_502(self):
        """POST /api/v1/instrument/onboard returns 502 when yfinance network error occurs."""
        from fastapi import HTTPException as FastAPIHTTPException

        app, client, session, engine = _make_client()
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                side_effect=FastAPIHTTPException(
                    status_code=502,
                    detail="Yahoo Finance is currently unreachable.",
                ),
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=_VALID_ONBOARD_PAYLOAD)

            assert response.status_code == 502
            assert "unreachable" in response.json().get("detail", "").lower()
        finally:
            _cleanup(app, session, engine)

    def test_onboard_missing_required_fields_returns_422(self):
        """POST /api/v1/instrument/onboard with missing body fields returns 422."""
        app, client, session, engine = _make_client()
        try:
            # Omit required fields: name, exchange, currency, country_code
            response = client.post("/api/v1/instrument/onboard", json={"ticker": "RELIANCE.NS"})
            assert response.status_code == 422
        finally:
            _cleanup(app, session, engine)

    def test_onboard_lot_size_is_optional(self):
        """POST /api/v1/instrument/onboard succeeds when lot_size is omitted."""
        app, client, session, engine = _make_client()
        payload = {k: v for k, v in _VALID_ONBOARD_PAYLOAD.items() if k != "lot_size"}
        try:
            with patch(
                "rita.api.v1.workflow.instrument_onboard.InstrumentRepository",
            ) as MockRepo, patch(
                "rita.api.v1.workflow.instrument_onboard.fetch_raw_data",
                return_value=(Path("/data/raw/RELIANCE.NS/reliance.ns_daily.csv"), 3800),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.process_to_input",
                return_value=Path("/data/input/RELIANCE.NS/reliance.ns_daily.csv"),
            ), patch(
                "rita.api.v1.workflow.instrument_onboard.seed_market_cache",
                return_value=120,
            ):
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                MockRepo.return_value = mock_repo_instance

                response = client.post("/api/v1/instrument/onboard", json=payload)

            assert response.status_code == 200
        finally:
            _cleanup(app, session, engine)


# ===========================================================================
# Contract verification — service layer (search_tickers return shape)
# ===========================================================================

class TestSearchTickersServiceContract:
    """Verify search_tickers() output keys match the API contract without HTTP layer."""

    def test_search_tickers_output_keys_match_contract(self):
        """search_tickers() returns dicts with all 6 contract-specified keys.

        The service imports yfinance locally inside the function body (``import yfinance as yf``),
        so there is no module-level ``yf`` attribute to patch.  We patch ``yfinance.Search``
        at the top of the yfinance package itself instead.
        """
        mock_quotes = [
            {
                "symbol":    "RELIANCE.NS",
                "longname":  "Reliance Industries Limited",
                "exchange":  "NSI",
                "currency":  "INR",
                "country":   "India",
                "quoteType": "EQUITY",
            },
            {
                "symbol":    "IDFC.NS",
                "longname":  "IDFC Limited",
                "exchange":  "NSI",
                "currency":  "INR",
                "country":   "India",
                "quoteType": "MUTUALFUND",   # should be filtered out
            },
        ]

        mock_search_instance = MagicMock()
        mock_search_instance.quotes = mock_quotes

        # yfinance is imported locally inside search_tickers(), so patch the
        # Search class on the yfinance package directly.
        with patch("yfinance.Search", return_value=mock_search_instance):
            from rita.services.instrument_onboard import search_tickers
            results = search_tickers("reliance")

        assert len(results) == 1, "Non-EQUITY results must be filtered out"
        item = results[0]
        assert set(item.keys()) == _SEARCH_FRONTEND_FIELDS
        assert item["quote_type"] == "EQUITY"
        assert item["ticker"] == "RELIANCE.NS"
        assert item["name"] == "Reliance Industries Limited"
