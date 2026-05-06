import json
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_runs(runs_dir: Path) -> list:
    runs = []
    for f in sorted(runs_dir.glob("run-*.json")):
        with open(f) as fp:
            runs.append(json.load(fp))
    return runs


def compute_per_role(runs: list) -> dict:
    role_data: dict = defaultdict(list)
    for run in runs:
        if run.get("skill_file", "n/a") == "n/a":
            continue  # exclude game runs — their agent entries are synthetic, not real pipeline agents
        for agent in run["agents"]:
            role_data[agent["role"]].append(agent)

    result = {}
    for role, agents in role_data.items():
        first_pass = [1 if a["status"] == "pass" else 0 for a in agents]
        result[role] = {
            "run_count": len(agents),
            "avg_adherence_score": round(
                sum(a["adherence_score"] for a in agents) / len(agents), 3
            ),
            "first_pass_rate": round(sum(first_pass) / len(first_pass), 3),
            "avg_token_cost": round(
                sum(a["token_estimate"] for a in agents) / len(agents)
            ),
        }
    return result


def compute_per_app(runs: list) -> dict:
    app_data: dict = defaultdict(list)
    for run in runs:
        app_data[run["app"]].append(run)

    result = {}
    for app, app_runs in app_data.items():
        status_counts: dict = defaultdict(int)
        for r in app_runs:
            status_counts[r["overall_status"]] += 1
        result[app] = {
            "run_count": len(app_runs),
            "pass": status_counts["pass"],
            "pass_with_warnings": status_counts["pass_with_warnings"],
            "fail": status_counts["fail"],
        }
    return result


def compute_grounding_trend(runs: list) -> list:
    trend = []
    for run in runs:
        if run.get("skill_file", "n/a") == "n/a":
            continue  # exclude game sessions — only pipeline builds appear in Run History
        total = 0
        passed = 0
        for agent in run["agents"]:
            for val in agent["grounding_checks"].values():
                total += 1
                if val is True:
                    passed += 1
        trend.append(
            {
                "run_id": run["run_id"],
                "app": run["app"],
                "grounding_score": round(passed / total, 3) if total else 0.0,
                "checks_passed": passed,
                "checks_total": total,
            }
        )
    return trend


def compute_failure_modes(runs: list) -> dict:
    counts: dict = defaultdict(lambda: defaultdict(int))
    for run in runs:
        if run.get("skill_file", "n/a") == "n/a":
            continue  # exclude game sessions
        for agent in run["agents"]:
            for fm in agent.get("failure_modes", []):
                counts[fm][agent["role"]] += 1

    return {
        fm: {"total": sum(roles.values()), "by_role": dict(roles)}
        for fm, roles in counts.items()
    }


def compute_game_sessions(runs: list) -> list:
    sessions = []
    for run in runs:
        if run.get("skill_file", "n/a") != "n/a" or run.get("app") != "invest-game":
            continue
        day_log = run.get("day_log", [])
        flagged = sum(1 for d in day_log if d.get("compliance_status") == "flagged")
        sessions.append(
            {
                "run_id": run["run_id"],
                "request": run.get("request", ""),
                "overall_status": run.get("overall_status", ""),
                "duration_minutes": run.get("duration_minutes", 0),
                "day_count": len(day_log),
                "flagged_count": flagged,
            }
        )
    return sorted(sessions, key=lambda s: s["run_id"], reverse=True)


def compute_skill_version_history(repo_root: Path) -> list:
    skill_files = [
        "project-office/skills/skill-add-rita-feature.md",
        "project-office/skills/skill-add-fno-feature.md",
        "project-office/skills/skill-add-ops-feature.md",
    ]
    result = []
    for sf in skill_files:
        try:
            log = subprocess.check_output(
                ["git", "log", "--oneline", "-5", "--", sf],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            commits = []
            for line in log.strip().splitlines():
                if line:
                    hash_part, *rest = line.split(" ", 1)
                    commits.append(
                        {"hash": hash_part, "message": rest[0] if rest else ""}
                    )
        except Exception:
            commits = []
        result.append(
            {
                "skill_file": sf,
                "last_updated": commits[0]["hash"] if commits else "unknown",
                "recent_commits": commits,
            }
        )
    return result


def main() -> None:
    script_dir = Path(__file__).parent
    runs_dir = script_dir / "runs"
    # script_dir = riia-ai-org/agent-ops/  →  parent.parent = riia-cowork-jun/
    repo_root = script_dir.parent.parent

    runs = load_runs(runs_dir)

    if not runs:
        print("No run-*.json files found in runs/ — writing empty metrics.")

    metrics = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_runs": len(runs),
        "per_role": compute_per_role(runs),
        "per_app": compute_per_app(runs),
        "grounding_trend": compute_grounding_trend(runs),
        "failure_modes": compute_failure_modes(runs),
        "skill_version_history": compute_skill_version_history(repo_root),
        "game_sessions": compute_game_sessions(runs),
    }

    output_path = script_dir / "metrics.json"
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"OK: metrics.json written -- {len(runs)} run(s) aggregated")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()
