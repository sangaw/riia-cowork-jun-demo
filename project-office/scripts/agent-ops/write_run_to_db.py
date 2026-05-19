#!/usr/bin/env python3
"""Write an /enhance run log JSON to the agent_build_runs database."""
import argparse
import json
import sys
from pathlib import Path

# Locate riia-jun-release/ relative to this script and add src/ to sys.path
_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parents[2]
_app_src = _repo_root / "riia-jun-release" / "src"
if str(_app_src) not in sys.path:
    sys.path.insert(0, str(_app_src))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from rita.repositories.agent_builds import AgentBuildRepository  # noqa: E402

_DB_PATH = _repo_root / "riia-jun-release" / "rita_output" / "rita.db"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write /enhance run log to DB")
    parser.add_argument("run_json_path", help="Path to run-YYYYMMDD-HHMM.json")
    parser.add_argument(
        "--actual-tokens",
        type=int,
        default=None,
        help="Actual total tokens used by this run",
    )
    args = parser.parse_args()

    run_path = Path(args.run_json_path)
    if not run_path.exists():
        print(f"ERROR: File not found: {run_path}", file=sys.stderr)
        return 1

    with open(run_path) as f:
        run_data = json.load(f)

    # Validate required fields
    for field in ("run_id", "app", "overall_status"):
        if field not in run_data:
            print(f"ERROR: Missing required field '{field}' in {run_path}", file=sys.stderr)
            return 1

    # If --actual-tokens provided, inject into each agent's actual_tokens and rewrite JSON
    if args.actual_tokens is not None:
        for agent in run_data.get("agents", []):
            agent["actual_tokens"] = {"total_tokens": args.actual_tokens}
        with open(run_path, "w") as f:
            json.dump(run_data, f, indent=2)

    try:
        engine = create_engine(
            f"sqlite:///{_DB_PATH}",
            connect_args={"check_same_thread": False},
        )
        db = Session(engine)
        repo = AgentBuildRepository(db)

        run_record = {
            "run_id": run_data["run_id"],
            "app": run_data["app"],
            "request": run_data.get("request", ""),
            "overall_status": run_data["overall_status"],
            "total_tokens_estimated": run_data.get("total_tokens_estimated"),
            "duration_minutes": run_data.get("duration_minutes"),
            "branch": run_data.get("branch", ""),
            "merge_status": run_data.get("merge_status", ""),
        }
        repo.upsert_run(run_record)

        agents = run_data.get("agents", [])
        repo.upsert_agents(
            run_id=run_data["run_id"],
            agents=agents,
            actual_tokens_total=args.actual_tokens,
        )
        db.close()

        print(f"DB write complete: run_id={run_data['run_id']}, agents={len(agents)}")
        return 0

    except OperationalError as exc:
        print(
            f"ERROR: DB operation failed — {exc}\n"
            "Hint: run `python -m alembic upgrade head` from riia-jun-release/ first.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
