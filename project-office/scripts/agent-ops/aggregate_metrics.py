import json
import logging
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


def load_runs(runs_dir: Path) -> list:
    runs = []
    for f in sorted(runs_dir.glob("run-*.json")):
        with open(f) as fp:
            runs.append(json.load(fp))
    return runs


def compute_per_role(runs: list) -> dict:
    role_data: dict = defaultdict(list)
    recent_role_data: dict = defaultdict(list)

    pipeline_runs = [r for r in runs if r.get("skill_file", "n/a") != "n/a"]
    recent_pipeline_runs = pipeline_runs[-5:]

    for run in pipeline_runs:
        for agent in run["agents"]:
            role_data[agent["role"]].append(agent)

    for run in recent_pipeline_runs:
        for agent in run["agents"]:
            recent_role_data[agent["role"]].append(agent)

    result = {}
    for role, agents in role_data.items():
        first_pass = [1 if a["status"] == "pass" else 0 for a in agents]
        recent_agents = recent_role_data.get(role, [])
        recent_fp = [1 if a["status"] == "pass" else 0 for a in recent_agents]
        result[role] = {
            "run_count": len(agents),
            "avg_adherence_score": round(
                sum(a["adherence_score"] for a in agents) / len(agents), 3
            ),
            "first_pass_rate": round(sum(first_pass) / len(first_pass), 3),
            "recent_first_pass_rate": round(sum(recent_fp) / len(recent_fp), 3) if recent_fp else None,
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
    recent_counts: dict = defaultdict(lambda: defaultdict(int))

    pipeline_runs = [r for r in runs if r.get("skill_file", "n/a") != "n/a"]
    recent_runs = pipeline_runs[-5:]  # last 5 pipeline runs only

    for run in pipeline_runs:
        for agent in run["agents"]:
            for fm in agent.get("failure_modes", []):
                counts[fm][agent["role"]] += 1

    for run in recent_runs:
        for agent in run["agents"]:
            for fm in agent.get("failure_modes", []):
                recent_counts[fm][agent["role"]] += 1

    return {
        fm: {
            "total": sum(roles.values()),
            "recent_fires": sum(recent_counts.get(fm, {}).values()),
            "by_role": dict(roles),
        }
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


def compute_task_completion(runs: list) -> dict:
    total = len(runs)
    if total == 0:
        return {
            "tsr": None,
            "first_attempt_success_rate": None,
            "partial_completion_rate": None,
            "abandonment_rate": None,
        }
    passed = sum(1 for r in runs if r.get("overall_status") == "pass")
    first_attempt = sum(
        1 for r in runs
        if r.get("retry_count", 0) == 0 and r.get("overall_status") == "pass"
    )
    partial = sum(1 for r in runs if r.get("overall_status") == "pass_with_warnings")
    abandoned = sum(1 for r in runs if r.get("abandoned", False))
    return {
        "tsr": round(passed / total, 3),
        "first_attempt_success_rate": round(first_attempt / total, 3),
        "partial_completion_rate": round(partial / total, 3),
        "abandonment_rate": round(abandoned / total, 3),
    }


def compute_quality(runs: list) -> dict:
    accuracy = [
        r["human_score"]["accuracy"]
        for r in runs
        if r.get("human_score") and r["human_score"].get("accuracy") is not None
    ]
    relevance = [
        r["human_score"]["relevance"]
        for r in runs
        if r.get("human_score") and r["human_score"].get("relevance") is not None
    ]
    csat = [
        r["human_score"]["csat"]
        for r in runs
        if r.get("human_score") and r["human_score"].get("csat") is not None
    ]
    recent_csat = csat[-3:] if len(csat) >= 3 else csat
    planning = [
        r["human_score"]["planning_ok"]
        for r in runs
        if r.get("human_score") and r["human_score"].get("planning_ok") is not None
    ]
    recent_planning = planning[-3:] if len(planning) >= 3 else planning
    grounding_scores = []
    for r in runs:
        for agent in r.get("agents", []):
            checks = agent.get("grounding_checks", {})
            if checks:
                vals = [v for v in checks.values() if isinstance(v, bool)]
                if vals:
                    grounding_scores.append(sum(vals) / len(vals))
    return {
        "avg_accuracy_score": round(sum(accuracy) / len(accuracy), 2) if accuracy else None,
        "avg_relevance_score": round(sum(relevance) / len(relevance), 2) if relevance else None,
        "avg_csat": round(sum(csat) / len(csat), 2) if csat else None,
        "recent_avg_csat": round(sum(recent_csat) / len(recent_csat), 2) if recent_csat else None,
        "csat_count": len(csat),
        "planning_accuracy_rate": (
            round(sum(1 for p in planning if p) / len(planning), 3) if planning else None
        ),
        "recent_planning_accuracy_rate": (
            round(sum(1 for p in recent_planning if p) / len(recent_planning), 3) if recent_planning else None
        ),
        "grounding_pass_rate": (
            round(sum(grounding_scores) / len(grounding_scores), 3) if grounding_scores else None
        ),
    }


def compute_token_forecasting(runs: list) -> dict:
    errors = []
    by_complexity: dict[str, list] = {"small": [], "medium": [], "large": []}
    by_feature_type: dict[str, list] = {
        "rita": [], "ops": [], "fno": [], "invest-game": []
    }
    for r in runs:
        estimated = r.get("total_tokens_estimated")
        # actual: prefer run-level total_actual_tokens, then per-agent sum, then fall back to estimated
        actual = r.get("total_actual_tokens")
        if actual is None:
            actual_sum = sum(
                a["actual_tokens"]["total_tokens"]
                for a in r.get("agents", [])
                if a.get("actual_tokens") and isinstance(a["actual_tokens"], dict)
                and a["actual_tokens"].get("total_tokens") is not None
            )
            actual = actual_sum if actual_sum > 0 else None
        # Compute forecast error whenever we have both actual and estimated
        if actual and estimated:
            err = abs(actual - estimated) / estimated * 100
            errors.append(err)
        # Bucket by complexity/feature_type using actual (or estimated as fallback)
        bucket_val = actual if actual else estimated
        tf = r.get("token_forecast")
        if tf and bucket_val:
            c = tf.get("complexity")
            if c in by_complexity:
                by_complexity[c].append(bucket_val)
            ft = tf.get("feature_type")
            if ft in by_feature_type:
                by_feature_type[ft].append(bucket_val)
        elif bucket_val:
            app = r.get("app")
            if app in by_feature_type:
                by_feature_type[app].append(bucket_val)
    multipliers = {"small": 0.7, "medium": 1.0, "large": 1.5}
    modifiers = {"rita": 1.0, "ops": 0.6, "fno": 0.8, "invest-game": 1.1}
    return {
        "avg_forecast_error_pct": round(sum(errors) / len(errors), 1) if errors else None,
        "by_complexity": {
            k: {
                "avg_actual": round(sum(v) / len(v)) if v else None,
                "multiplier": multipliers[k],
            }
            for k, v in by_complexity.items()
        },
        "by_feature_type": {
            k: {
                "run_count": len(v),
                "avg_tokens": round(sum(v) / len(v)) if v else None,
                "modifier": modifiers[k],
            }
            for k, v in by_feature_type.items()
        },
    }


def compute_efficiency(runs: list) -> dict:
    durations = [r["duration_minutes"] for r in runs if r.get("duration_minutes") is not None]
    # Prefer actual tokens when available; fall back to estimated
    tokens = [
        r.get("total_actual_tokens") or r["total_tokens_estimated"]
        for r in runs
        if r.get("total_actual_tokens") is not None or r.get("total_tokens_estimated") is not None
    ]
    retries = [r.get("retry_count", 0) for r in runs]
    time_saved = [
        r["human_score"]["time_saved_hours"]
        for r in runs
        if r.get("human_score") and r["human_score"].get("time_saved_hours") is not None
    ]
    return {
        "avg_duration_minutes": round(sum(durations) / len(durations)) if durations else None,
        "avg_tokens_per_run": round(sum(tokens) / len(tokens)) if tokens else None,
        "avg_retry_count": round(sum(retries) / len(retries), 2) if retries else None,
        "avg_time_saved_hours": round(sum(time_saved) / len(time_saved), 1) if time_saved else None,
    }


def compute_reliability(runs: list) -> dict:
    total_fc = 0
    recovered = 0
    pw_warnings = sum(1 for r in runs if r.get("overall_status") == "pass_with_warnings")
    fails = sum(1 for r in runs if r.get("overall_status") == "fail")
    loop_total = sum(r.get("loop_events", 0) for r in runs)
    for r in runs:
        for agent in r.get("agents", []):
            fms = agent.get("failure_modes", [])
            if fms:
                total_fc += len(fms)
                if agent.get("status") != "fail":
                    recovered += len(fms)
    denom = pw_warnings + fails
    return {
        "error_recovery_rate": round(recovered / total_fc, 3) if total_fc > 0 else None,
        "graceful_degradation_rate": round(pw_warnings / denom, 3) if denom > 0 else None,
        "loop_event_total": loop_total,
    }


def compute_hitl(runs: list) -> dict:
    total = len(runs)
    if total == 0:
        return {"escalation_rate": None, "avg_corrections_per_run": None, "total_hitl_events": 0}
    escalated = sum(1 for r in runs if r.get("hitl_events"))
    corrections = sum(
        sum(1 for e in r.get("hitl_events", []) if e.get("type") == "correction")
        for r in runs
    )
    total_events = sum(len(r.get("hitl_events", [])) for r in runs)
    return {
        "escalation_rate": round(escalated / total, 3),
        "avg_corrections_per_run": round(corrections / total, 2),
        "total_hitl_events": total_events,
    }


def compute_agentic(runs: list) -> dict:
    context_scores = []
    memory_used_flags = []
    for r in runs:
        for agent in r.get("agents", []):
            checks = agent.get("grounding_checks", {})
            if "plan_status_read" in checks and "spec_reference_valid" in checks:
                both = int(checks["plan_status_read"]) + int(checks["spec_reference_valid"])
                context_scores.append(both / 2)
            if agent.get("role") == "engineer" and "memory_used" in checks:
                memory_used_flags.append(bool(checks["memory_used"]))
    loop_total = sum(r.get("loop_events", 0) for r in runs)
    total_runs = len(runs)
    return {
        "context_adherence_rate": (
            round(sum(context_scores) / len(context_scores), 3) if context_scores else None
        ),
        "memory_utilization_rate": (
            round(sum(memory_used_flags) / len(memory_used_flags), 3) if memory_used_flags else None
        ),
        "loop_detection_rate": round(loop_total / total_runs, 3) if total_runs > 0 else None,
    }


def compute_skill_version_history(repo_root: Path) -> list:
    skill_files = [
        "project-office/skills/skill-add-rita-feature.md",
        "project-office/skills/skill-add-fno-feature.md",
        "project-office/skills/skill-add-ops-feature.md",
    ]
    result = []
    for sf in skill_files:
        try:
            proc = subprocess.run(
                ["git", "log", "--oneline", "-5", "--", sf],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                log.error("subprocess failed", extra={"stderr": proc.stderr})
                commits = []
            else:
                commits = []
                for line in proc.stdout.strip().splitlines():
                    if line:
                        hash_part, *rest = line.split(" ", 1)
                        commits.append(
                            {"hash": hash_part, "message": rest[0] if rest else ""}
                        )
        except Exception:
            log.error("git log failed", exc_info=True)
            commits = []
        result.append(
            {
                "skill_file": sf,
                "last_updated": commits[0]["hash"] if commits else "unknown",
                "recent_commits": commits,
            }
        )
    return result


def compute_api_metrics(db_path: Path) -> dict:
    """Read api_call_log table via sqlite3 and return aggregate metrics."""
    import sqlite3
    from datetime import timezone

    if not db_path.exists():
        return {"available": False}
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "api_call_log" not in tables:
            con.close()
            return {"available": False}
        rows = cur.execute(
            "SELECT path, method, status_code, duration_ms, called_at FROM api_call_log"
        ).fetchall()
        con.close()
        if not rows:
            return {
                "available": True,
                "total_calls": 0,
                "unique_endpoints": 0,
                "overall_error_rate_pct": 0.0,
                "top_5_by_calls": [],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        grouped: dict = defaultdict(list)
        for path, method, status_code, duration_ms, called_at in rows:
            grouped[(path, method)].append((status_code, duration_ms))
        total_calls = len(rows)
        error_count = sum(1 for _, _, sc, _, _ in rows if sc and sc >= 400)
        error_5xx = sum(1 for _, _, sc, _, _ in rows if sc and sc >= 500)
        endpoint_stats = []
        for (path, method), calls in grouped.items():
            durations = sorted([d for _, d in calls if d is not None])
            n = len(durations)
            p50 = durations[n // 2] if n else None
            p95 = durations[int(n * 0.95)] if n else None
            errs = sum(1 for sc, _ in calls if sc and sc >= 400)
            endpoint_stats.append(
                {
                    "path": path,
                    "method": method,
                    "count": len(calls),
                    "p50_ms": round(p50, 1) if p50 is not None else None,
                    "p95_ms": round(p95, 1) if p95 is not None else None,
                    "error_count": errs,
                }
            )
        endpoint_stats.sort(key=lambda x: x["count"], reverse=True)
        overall_error_rate = round(error_count / total_calls * 100, 2) if total_calls else 0.0
        rate_5xx = round(error_5xx / total_calls * 100, 2) if total_calls else 0.0
        # Alert on 4xx+5xx combined only above 15% (4xx are expected client errors for this app)
        # Alert on 5xx alone above 2% (server errors are always actionable)
        if overall_error_rate > 15.0:
            print(f"[ALERT] API error rate {overall_error_rate}% above 15% threshold")
        if rate_5xx > 2.0:
            print(f"[ALERT] API 5xx error rate {rate_5xx}% above 2% threshold — server errors require investigation")
        return {
            "available": True,
            "total_calls": total_calls,
            "unique_endpoints": len(grouped),
            "overall_error_rate_pct": overall_error_rate,
            "error_rate_5xx_pct": rate_5xx,
            "top_5_by_calls": endpoint_stats[:5],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def main() -> None:
    # __file__ = project-office/scripts/agent-ops/aggregate_metrics.py
    # .parents[3] = riia-cowork-jun/
    _data_dir = Path(__file__).resolve().parents[3] / "riia-jun-release" / "data" / "agent-ops"
    runs_dir = _data_dir / "runs"
    # script_dir.parent.parent.parent = riia-cowork-jun/ for git log calls
    repo_root = Path(__file__).resolve().parents[3]

    output_path = _data_dir / "metrics.json"
    runs = load_runs(runs_dir)

    if not runs:
        log.info("No run-*.json files found in runs/ — writing empty metrics.")

    skill_version_history = compute_skill_version_history(repo_root)
    # Preserve improvement fields from existing metrics.json so manual entries survive re-runs
    existing_improvements = {}
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
            for entry in existing.get("skill_version_history", []):
                key = entry.get("skill_file")
                if key:
                    existing_improvements[key] = {
                        k: entry[k] for k in ("improvement_applied", "before_first_pass_rate", "after_first_pass_rate") if k in entry
                    }
        except Exception:
            pass
    computed_keys = {e.get("skill_file") for e in skill_version_history}
    for entry in skill_version_history:
        preserved = existing_improvements.get(entry.get("skill_file"), {})
        entry.setdefault("improvement_applied", preserved.get("improvement_applied"))
        entry.setdefault("before_first_pass_rate", preserved.get("before_first_pass_rate"))
        entry.setdefault("after_first_pass_rate", preserved.get("after_first_pass_rate"))
    # Carry over entries for files not in the computed list (e.g. enhance.md)
    for key, preserved in existing_improvements.items():
        if key not in computed_keys and preserved.get("improvement_applied"):
            skill_version_history.append({"skill_file": key, **preserved})

    db_path = repo_root / "riia-jun-release" / "rita_output" / "rita.db"
    metrics = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_runs": len(runs),
        "per_role": compute_per_role(runs),
        "per_app": compute_per_app(runs),
        "grounding_trend": compute_grounding_trend(runs),
        "failure_modes": compute_failure_modes(runs),
        "skill_version_history": skill_version_history,
        "game_sessions": compute_game_sessions(runs),
        "task_completion": compute_task_completion(runs),
        "quality": compute_quality(runs),
        "token_forecasting": compute_token_forecasting(runs),
        "efficiency": compute_efficiency(runs),
        "reliability": compute_reliability(runs),
        "hitl": compute_hitl(runs),
        "agentic": compute_agentic(runs),
        "api_metrics": compute_api_metrics(db_path),
    }

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    log.info("metrics.json written", runs=len(runs), output=str(output_path))

    # Threshold alerts — alert only on recent evidence, not cumulative history
    fc_counts = metrics.get("failure_modes", {})
    for fc_code, fc_data in fc_counts.items():
        if not isinstance(fc_data, dict):
            continue
        recent = fc_data.get("recent_fires", 0)
        total = fc_data.get("total", 0)
        if recent > 0:
            print(f"[ALERT] {fc_code} fired {recent}x in last 5 runs (total all-time: {total}) — review skill file rule")

    for role_name, role_data in metrics.get("per_role", {}).items():
        if isinstance(role_data, dict):
            # Alert on recent rate (last 5 runs) — all-time rate lags behind improvements
            fpr = role_data.get("recent_first_pass_rate")
            all_time = role_data.get("first_pass_rate", 0)
            if fpr is not None and fpr < 0.70:
                print(
                    f"[ALERT] {role_name} recent first-pass rate {round(fpr * 100)}%"
                    f" (all-time: {round(all_time * 100)}%) — grounding checks need review"
                )

    csat_count = metrics.get("quality", {}).get("csat_count", 0)
    recent_avg_csat = metrics.get("quality", {}).get("recent_avg_csat")
    avg_csat = metrics.get("quality", {}).get("avg_csat")
    # Use recent_avg_csat (last 3) when available — all-time drags from early sessions
    csat_check = recent_avg_csat if recent_avg_csat is not None else avg_csat
    if csat_check is not None and csat_count >= 3 and csat_check < 3.5:
        label = "recent (last 3)" if recent_avg_csat is not None else "all-time"
        print(f"[ALERT] CSAT {csat_check}/5 {label} below threshold ({csat_count} runs rated) — review last 3 runs")

    avg_forecast_err = metrics.get("token_forecasting", {}).get("avg_forecast_error_pct")
    if avg_forecast_err is not None and avg_forecast_err > 35:
        print(
            f"[ALERT] Token forecast off by {avg_forecast_err}%"
            " on average — recalibrate multipliers"
        )


if __name__ == "__main__":
    main()
