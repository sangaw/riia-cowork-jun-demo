"""Unit tests for CsvRepository via PositionsRepository.

All tests are isolated via tmp_path — no shared file state between tests.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test fixture helpers
# ---------------------------------------------------------------------------

def make_position(n: int):
    """Return a minimal but realistic Position record."""
    from rita.schemas.positions import Position

    return Position(
        position_id=f"pos-{n}",
        instrument=f"NIFTY{n}CE",
        underlying="NIFTY",
        quantity=75,
        avg_price=100.0,
        last_traded_price=105.0,
        pnl=375.0,
        recorded_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
    )


def make_repo(data_dir: Path):
    """Construct a PositionsRepository scoped to data_dir."""
    from rita.repositories.positions import PositionsRepository

    return PositionsRepository(data_dir=data_dir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReadAllEmptyWhenNoFile:
    def test_read_all_empty_when_no_file(self, tmp_path: Path):
        """Repository returns [] when the CSV file does not exist."""
        repo = make_repo(tmp_path)
        assert repo.read_all() == []


class TestWriteAndReadRoundTrip:
    def test_write_and_read_round_trip(self, tmp_path: Path):
        """Write a list of Position records, read them back, assert equal."""
        repo = make_repo(tmp_path)
        records = [make_position(i) for i in range(3)]

        repo.write_all(records)
        result = repo.read_all()

        assert len(result) == 3
        result_ids = {r.position_id for r in result}
        assert result_ids == {"pos-0", "pos-1", "pos-2"}

        # Spot-check a field that survives CSV serialisation
        for original in records:
            match = next(r for r in result if r.position_id == original.position_id)
            assert match.quantity == original.quantity
            assert match.pnl == original.pnl


class TestUpsertInsertsNewRecord:
    def test_upsert_inserts_new_record(self, tmp_path: Path):
        """Upsert a record not yet in the file; read_all contains it."""
        repo = make_repo(tmp_path)
        pos = make_position(1)

        repo.upsert(pos)
        result = repo.read_all()

        assert len(result) == 1
        assert result[0].position_id == "pos-1"


class TestUpsertReplacesExisting:
    def test_upsert_replaces_existing(self, tmp_path: Path):
        """Upsert a record with the same id; old value is replaced."""
        repo = make_repo(tmp_path)
        original = make_position(1)
        repo.upsert(original)

        updated = make_position(1)
        # Mutate one field so we can tell them apart
        updated = updated.model_copy(update={"avg_price": 200.0})
        repo.upsert(updated)

        result = repo.read_all()
        assert len(result) == 1
        assert result[0].avg_price == 200.0


class TestDeleteRemovesRecord:
    def test_delete_removes_record(self, tmp_path: Path):
        """Delete by id; record is gone from read_all."""
        repo = make_repo(tmp_path)
        for i in range(3):
            repo.upsert(make_position(i))

        removed = repo.delete("pos-1")

        assert removed is True
        ids = {r.position_id for r in repo.read_all()}
        assert "pos-1" not in ids
        assert "pos-0" in ids
        assert "pos-2" in ids


class TestDeleteReturnsFalseWhenNotFound:
    def test_delete_returns_false_when_not_found(self, tmp_path: Path):
        """Delete a non-existent id returns False."""
        repo = make_repo(tmp_path)
        repo.upsert(make_position(1))

        result = repo.delete("pos-999")

        assert result is False
        assert len(repo.read_all()) == 1


class TestFindByIdReturnsCorrect:
    def test_find_by_id_returns_correct(self, tmp_path: Path):
        """find_by_id returns the right record."""
        repo = make_repo(tmp_path)
        for i in range(5):
            repo.upsert(make_position(i))

        found = repo.find_by_id("pos-3")

        assert found is not None
        assert found.position_id == "pos-3"
        assert found.instrument == "NIFTY3CE"


class TestFindByIdReturnsNoneWhenMissing:
    def test_find_by_id_returns_none_when_missing(self, tmp_path: Path):
        """find_by_id returns None for an unknown id."""
        repo = make_repo(tmp_path)
        repo.upsert(make_position(1))

        result = repo.find_by_id("pos-999")

        assert result is None


class TestValidationErrorOnBadRow:
    def test_validation_error_on_bad_row(self, tmp_path: Path):
        """
        A CSV with a deliberately missing required column triggers
        RepositoryValidationError on read_all.
        """
        from rita.repositories.base import RepositoryValidationError

        csv_path = tmp_path / "positions.csv"
        # Write a CSV that is missing the required 'underlying' column
        csv_path.write_text(
            "position_id,instrument,quantity,avg_price,last_traded_price,pnl,recorded_at\n"
            "pos-bad,NIFTY1CE,75,100.0,105.0,375.0,2026-03-31T09:00:00+00:00\n",
            encoding="utf-8",
        )

        repo = make_repo(tmp_path)

        with pytest.raises(RepositoryValidationError):
            repo.read_all()


class TestWriteEmptyListCreatesHeaderFile:
    def test_write_empty_list_creates_header_file(self, tmp_path: Path):
        """write_all([]) creates a CSV with headers but no data rows."""
        repo = make_repo(tmp_path)
        repo.write_all([])

        csv_path = tmp_path / "positions.csv"
        assert csv_path.exists()

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        # Should have exactly the header line
        assert len(lines) == 1
        header_fields = lines[0].split(",")
        assert "position_id" in header_fields
        assert "instrument" in header_fields


class TestConcurrentUpsertsNoCorruption:
    def test_concurrent_upserts_no_corruption(self, tmp_path: Path):
        """
        10 threads each upsert a distinct record simultaneously.
        After all threads finish, read_all returns exactly 10 records
        with no duplicates or missing entries.
        """
        repo = make_repo(tmp_path)
        n_threads = 10
        barrier = threading.Barrier(n_threads)
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                barrier.wait()  # synchronise all threads to start at once
                repo.upsert(make_position(n))
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"

        result = repo.read_all()
        ids = {r.position_id for r in result}

        assert len(result) == n_threads, f"Expected {n_threads} records, got {len(result)}"
        assert ids == {f"pos-{i}" for i in range(n_threads)}
