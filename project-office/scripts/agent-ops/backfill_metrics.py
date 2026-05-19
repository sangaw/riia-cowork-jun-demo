"""backfill_metrics.py — Backfill new v2 fields into existing run-*.json files.

Adds the following fields ONLY IF not already present (never overwrites):
  - retry_count, abandoned, loop_events, hitl_events, human_score, token_forecast
  - Engineer grounding_checks.memory_used, grounding_checks.tool_error_handled

Invocation:
    python project-office/scripts/agent-ops/backfill_metrics.py

Must never touch any file under rita_input/.
"""

import glob
import json
import os
from pathlib import Path

# Role average token costs (historical averages used for proportional split)
ROLE_AVGS = {
    "pm": 7612,
    "architect": 9975,
    "engineer": 31112,
    "qa": 11300,
    "techwriter": 6650,
}
TOTAL_AVG = sum(ROLE_AVGS.values())  # 66649


def compute_token_forecast(run: dict, basis_runs: int) -> dict:
    """Compute a retrospective token forecast from total_tokens_estimated."""
    total = run.get("total_tokens_estimated", 0)

    if total < 30000:
        complexity, score = "small", 0.7
    elif total <= 60000:
        complexity, score = "medium", 1.0
    else:
        complexity, score = "large", 1.5

    feature_type = run.get("app", "rita")

    per_role = {
        role: round(total * (avg / TOTAL_AVG))
        for role, avg in ROLE_AVGS.items()
    }
    total_forecast = sum(per_role.values())

    confidence = "±25%" if basis_runs >= 5 else "±40%"

    return {
        "complexity": complexity,
        "complexity_score": score,
        "feature_type": feature_type,
        "per_role": per_role,
        "total_forecast": total_forecast,
        "confidence": confidence,
        "basis_runs": basis_runs,
    }


def main() -> None:
    # __file__ = project-office/scripts/agent-ops/backfill_metrics.py
    # .parents[3] = riia-cowork-jun/
    _data_dir = Path(__file__).resolve().parents[3] / "riia-jun-release" / "data" / "agent-ops"
    runs_dir = _data_dir / "runs"

    pattern = str(runs_dir / "run-*.json")
    run_files = sorted(glob.glob(pattern))

    # Safety guard — never touch rita_input/
    run_files = [f for f in run_files if "rita_input" not in f.replace(os.sep, "/")]

    if not run_files:
        print("No run-*.json files found. Nothing to backfill.")
        return

    # Track count of runs processed per feature_type to compute basis_runs
    feature_type_counts: dict[str, int] = {}

    n_backfilled = 0
    for run_path in run_files:
        with open(run_path) as f:
            data = json.load(f)

        modified = False

        # --- Top-level scalar fields ---
        if "retry_count" not in data:
            data["retry_count"] = 0
            modified = True

        if "abandoned" not in data:
            data["abandoned"] = False
            modified = True

        if "loop_events" not in data:
            data["loop_events"] = 0
            modified = True

        if "hitl_events" not in data:
            data["hitl_events"] = []
            modified = True

        if "human_score" not in data:
            data["human_score"] = {
                "accuracy": None,
                "relevance": None,
                "planning_ok": None,
                "csat": None,
                "time_saved_hours": None,
            }
            modified = True

        # --- token_forecast ---
        if "token_forecast" not in data:
            feature_type = data.get("app", "rita")
            basis_runs = feature_type_counts.get(feature_type, 0)
            data["token_forecast"] = compute_token_forecast(data, basis_runs)
            modified = True

        # Advance feature_type counter AFTER computing basis_runs for this run
        feature_type = data.get("app", "rita")
        feature_type_counts[feature_type] = feature_type_counts.get(feature_type, 0) + 1

        # --- Engineer grounding_checks ---
        for agent in data.get("agents", []):
            if agent.get("role") == "engineer":
                checks = agent.get("grounding_checks")
                if isinstance(checks, dict):
                    if "memory_used" not in checks:
                        checks["memory_used"] = False
                        modified = True
                    if "tool_error_handled" not in checks:
                        checks["tool_error_handled"] = False
                        modified = True

        if modified:
            with open(run_path, "w") as f:
                json.dump(data, f, indent=2)
            n_backfilled += 1

    print(f"Backfilled {n_backfilled} run files.")


if __name__ == "__main__":
    main()
