#!/usr/bin/env python3
"""
Generate a portfolio-level heatmap from snapshot JSON.

Outputs:
- outputs/portfolio_heatmap.csv  (matrix of initiatives x drivers; values 0-10)
- outputs/portfolio_heatmap.md   (quick markdown summary + top drivers)
"""

from __future__ import annotations
import json
import csv
import argparse
from typing import Dict, Any, List, Tuple


DRIVERS = [
    ("Confidence Risk", "confidence_risk"),     # higher is worse
    ("Blocked", "blocked"),
    ("Scope Volatility", "scope_volatility"),
    ("Dependencies", "dependencies"),
    ("Due Proximity", "due_proximity"),
    ("Stagnation", "stagnation"),
]


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_0_10(value: float, max_value: float) -> int:
    if max_value <= 0:
        return 0
    return int(round(clamp((value / max_value) * 10.0, 0.0, 10.0)))


def compute_driver_scores(item: Dict[str, Any]) -> Dict[str, int]:
    """
    Convert initiative fields into normalized (0-10) driver scores.
    All scores represent "risk intensity" (higher = worse).
    """
    dcs = int(item.get("dcs_current", 0))
    blocked_days = int(item.get("blocked_days", 0))
    scope_changes = int(item.get("scope_changes_14d", 0))
    deps = int(item.get("dependency_count", 0))
    critical_dep = bool(item.get("critical_dependency", False))
    days_to_target = int(item.get("days_to_target", 21))
    days_stagnant = int(item.get("days_stagnant", 0))

    # Confidence risk: invert DCS into a 0-10 scale (0 best, 10 worst)
    confidence_risk = score_0_10(100 - dcs, 60)  # 60pt spread = full scale

    # Blocked: 0-5 days maps to 0-10
    blocked = score_0_10(blocked_days, 5)

    # Scope volatility: 0-5 changes maps to 0-10
    scope_volatility = score_0_10(scope_changes, 5)

    # Dependencies: 0-6 deps maps to 0-10, +2 bump if critical dep (capped at 10)
    dependencies = score_0_10(deps, 6)
    if critical_dep:
        dependencies = min(10, dependencies + 2)

    # Due proximity: closer = higher risk
    # <=7 days => 10, <=14 => 7, <=21 => 4, else 1
    if days_to_target <= 7:
        due_proximity = 10
    elif days_to_target <= 14:
        due_proximity = 7
    elif days_to_target <= 21:
        due_proximity = 4
    else:
        due_proximity = 1

    # Stagnation: 0-6 days maps to 0-10
    stagnation = score_0_10(days_stagnant, 6)

    return {
        "confidence_risk": confidence_risk,
        "blocked": blocked,
        "scope_volatility": scope_volatility,
        "dependencies": dependencies,
        "due_proximity": due_proximity,
        "stagnation": stagnation,
    }


def load_snapshot(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: str, rows: List[Dict[str, Any]], headers: List[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    parser = argparse.ArgumentParser(description="Generate portfolio heatmap artifacts from snapshot JSON.")
    parser.add_argument("--input", required=True, help="Path to snapshot JSON.")
    parser.add_argument("--out-csv", required=True, help="Path to output CSV heatmap.")
    parser.add_argument("--out-md", required=True, help="Path to output Markdown summary.")
    args = parser.parse_args()

    snap = load_snapshot(args.input)
    week_ending = snap.get("portfolio", {}).get("week_ending", "unknown")
    inits = snap.get("initiatives", [])

    # Build heatmap rows
    heatmap_rows: List[Dict[str, Any]] = []
    driver_totals = {key: 0 for _, key in DRIVERS}

    for it in inits:
        name = it.get("name", it.get("id", "unknown"))
        d = compute_driver_scores(it)

        row = {"Initiative": name}
        for label, key in DRIVERS:
            row[label] = d[key]
            driver_totals[key] += d[key]

        heatmap_rows.append(row)

    # Sort worst-first by Confidence Risk then Due Proximity then Blocked
    heatmap_rows.sort(key=lambda r: (r["Confidence Risk"], r["Due Proximity"], r["Blocked"]), reverse=True)

    headers = ["Initiative"] + [label for label, _ in DRIVERS]
    write_csv(args.out_csv, heatmap_rows, headers)

    # Create markdown summary
    # Top drivers by portfolio total
    totals_ranked: List[Tuple[str, int]] = []
    for label, key in DRIVERS:
        totals_ranked.append((label, int(driver_totals[key])))
    totals_ranked.sort(key=lambda x: x[1], reverse=True)

    worst3 = heatmap_rows[:3] if len(heatmap_rows) >= 3 else heatmap_rows

    lines = []
    lines.append(f"# Portfolio Heatmap Summary — Week Ending {week_ending}")
    lines.append("")
    lines.append("## Highest Portfolio Risk Drivers (aggregate intensity)")
    for label, total in totals_ranked:
        lines.append(f"- **{label}**: {total}")
    lines.append("")
    lines.append("## Top 3 Initiatives by Combined Risk (from heatmap)")
    for r in worst3:
        lines.append(
            f"- **{r['Initiative']}** | Confidence {r['Confidence Risk']} | Due {r['Due Proximity']} | "
            f"Blocked {r['Blocked']} | Scope {r['Scope Volatility']} | Deps {r['Dependencies']} | Stagnation {r['Stagnation']}"
        )
    lines.append("")
    lines.append("> Scores are normalized 0–10 per driver (10 = highest risk intensity).")

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Wrote heatmap CSV: {args.out_csv}")
    print(f"✅ Wrote heatmap summary: {args.out_md}")


if __name__ == "__main__":
    main()
