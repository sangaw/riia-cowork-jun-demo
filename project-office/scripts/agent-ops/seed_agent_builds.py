"""One-time migration: import all run-*.json files into the agent_build_runs DB.

Run from riia-cowork-jun/ project root:
    python project-office/scripts/agent-ops/seed_agent_builds.py

Safe to re-run — skips runs already present in the DB (keyed on run_id).
"""
import json
import sys
from datetime import datetime
from pathlib import Path

repo_root = Path(__file__).parents[3]
sys.path.insert(0, str(repo_root / "riia-jun-release" / "src"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from rita.models.agent_builds import AgentBuildAgentModel, AgentBuildRunModel  # noqa: E402
from rita.database import Base  # noqa: E402

RUNS_DIR = repo_root / "riia-jun-release" / "data" / "agent-ops" / "runs"
DB_PATH = repo_root / "riia-jun-release" / "rita_output" / "rita.db"

engine = create_engine(f"sqlite:///{DB_PATH}")
Base.metadata.create_all(engine)


def seed():
    run_files = sorted(RUNS_DIR.glob("run-*.json"))
    if not run_files:
        print("No run files found.")
        return

    inserted_runs = 0
    inserted_agents = 0
    skipped = 0

    with Session(engine) as db:
        existing_ids = {r[0] for r in db.query(AgentBuildRunModel.run_id).all()}

        for path in run_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  SKIP {path.name}: {e}")
                continue

            run_id = data.get("run_id")
            if not run_id:
                print(f"  SKIP {path.name}: missing run_id")
                continue

            if run_id in existing_ids:
                skipped += 1
                continue

            db.add(AgentBuildRunModel(
                run_id=run_id,
                app=data.get("app", ""),
                request=data.get("request"),
                skill_file=data.get("skill_file"),
                overall_status=data.get("overall_status", "unknown"),
                total_tokens_estimated=data.get("total_tokens_estimated"),
                duration_minutes=data.get("duration_minutes"),
                branch=data.get("branch"),
                merge_status=data.get("merge_status"),
                merge_commit=data.get("merge_commit"),
                recorded_at=datetime.utcnow(),
            ))
            inserted_runs += 1

            for agent in data.get("agents", []):
                role = agent.get("role", "unknown")
                db.add(AgentBuildAgentModel(
                    agent_id=f"{run_id}-{role}",
                    run_id=run_id,
                    role=role,
                    status=agent.get("status", "unknown"),
                    steps_required=agent.get("steps_required"),
                    steps_completed=agent.get("steps_completed"),
                    adherence_score=agent.get("adherence_score"),
                    token_estimate=agent.get("token_estimate"),
                    grounding_checks=agent.get("grounding_checks"),
                    failure_modes=agent.get("failure_modes"),
                    recorded_at=datetime.utcnow(),
                ))
                inserted_agents += 1

        db.commit()

    print(f"Done. Inserted: {inserted_runs} runs, {inserted_agents} agent rows. Skipped (already in DB): {skipped}.")


if __name__ == "__main__":
    seed()
