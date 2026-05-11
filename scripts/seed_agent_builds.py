"""Seed script: read run-*.json files from riia-ai-org/agent-ops/runs/ and insert into DB.

Run from the repo root:
    python scripts/seed_agent_builds.py

Idempotent — skips run_ids that already exist in the database.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure src/ is on the Python path when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "riia-jun-release" / "src"))

from rita.database import SessionLocal
from rita.models.agent_builds import AgentBuildAgentModel, AgentBuildRunModel


def main() -> None:
    repo_root = Path(__file__).parent.parent
    runs_dir = repo_root / "riia-ai-org" / "agent-ops" / "runs"
    run_files = sorted(runs_dir.glob("run-*.json"))

    if not run_files:
        print(f"No run-*.json files found in {runs_dir}")
        return

    db = SessionLocal()
    try:
        seeded_runs = 0
        seeded_agents = 0

        for run_file in run_files:
            try:
                with run_file.open(encoding="utf-8") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"[SKIP] {run_file.name}: {exc}")
                continue

            run_id = data.get("run_id")
            if not run_id:
                print(f"[SKIP] {run_file.name}: missing run_id")
                continue

            existing = db.get(AgentBuildRunModel, run_id)
            if existing is not None:
                print(f"[SKIP] {run_id}: already in DB")
                continue

            run_row = AgentBuildRunModel(
                run_id=run_id,
                app=data.get("app", "unknown"),
                request=data.get("request"),
                skill_file=data.get("skill_file"),
                overall_status=data.get("overall_status", "unknown"),
                total_tokens_estimated=data.get("total_tokens_estimated"),
                duration_minutes=data.get("duration_minutes"),
                branch=data.get("branch"),
                merge_status=data.get("merge_status"),
                merge_commit=data.get("merge_commit"),
                recorded_at=datetime.utcnow(),
            )
            db.add(run_row)
            seeded_runs += 1

            for agent in data.get("agents", []):
                agent_row = AgentBuildAgentModel(
                    agent_id=str(uuid.uuid4()),
                    run_id=run_id,
                    role=agent.get("role", "unknown"),
                    status=agent.get("status", "unknown"),
                    steps_required=agent.get("steps_required"),
                    steps_completed=agent.get("steps_completed"),
                    adherence_score=agent.get("adherence_score"),
                    token_estimate=agent.get("token_estimate"),
                    grounding_checks=agent.get("grounding_checks"),
                    failure_modes=agent.get("failure_modes"),
                    recorded_at=datetime.utcnow(),
                )
                db.add(agent_row)
                seeded_agents += 1

        db.commit()
        print(f"Seeded {seeded_runs} runs, {seeded_agents} agent rows")
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
