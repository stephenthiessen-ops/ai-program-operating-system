#!/usr/bin/env python3
"""
Generate a 1-page executive brief from a structured weekly snapshot.

- No external dependencies
- Works with synthetic or real scored datasets
"""

from __future__ import annotations
import json
import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Tuple


@dataclass
class Initiative:
    id: str
    name: str
    dcs_current: int
    dcs_prior: int
    band: str
    blocked_days: int
    scope_changes_14d: int
    days_stagnant: int
    dependency_count: int
    critical_dependency: bool
    days_to_target: int
    status_notes: List[str]

    @property
    def delta(self) -> int:
        return self.dcs_current - self.dcs_prior


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def load_snapshot(path: str) -> Tuple[Dict[str, Any], List[Initiative]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    initiatives = []
    for x in raw.get("initiatives", []):
        initiatives.append(
            Initiative(
                id=x["id"],
                name=x["name"],
                dcs_current=int(x["dcs_current"]),
                dcs_prior=int(x["dcs_prior"]),
                band=x["band"],
                blocked_days=int(x["blocked_days"]),
                scope_changes_14d=int(x["scope_changes_14d"]),
                days_stagnant=int(x["days_stagnant"]),
                dependency_count=int(x["dependency_count"]),
                critical_dependency=bool(x["critical_dependency"]),
                days_to_target=int(x["days_to_target"]),
                status_notes=list(x.get("status_notes", [])),
            )
        )
    return raw.get("portfolio", {}), initiatives


def band_counts(initiatives: List[Initiative]) -> Dict[str, int]:
    counts = {"Green": 0, "Yellow": 0, "Red": 0}
    for i in initiatives:
        if i.band in counts:
            counts[i.band] += 1
        else:
            counts[i.band] = counts.get(i.band, 0) + 1
    return counts


def risk_rank(i: Initiative) -> float:
    """
    Heuristic for sorting risks:
    - prioritize falling confidence
    - near-term deadlines
    - blocked/stagnant work
    - critical dependencies
    """
    fall = max(0, -i.delta) * 3.0
    due = 0.0
    if i.days_to_target <= 7:
        due = 18.0
    elif i.days_to_target <= 14:
        due = 10.0

    blocked = clamp(i.blocked_days, 0, 10) * 4.0
    stagnant = clamp(i.days_stagnant, 0, 10) * 2.5
    deps = clamp(i.dependency_count, 0, 10) * 2.0 + (6.0 if i.critical_dependency else 0.0)

    # Lower scores should float up
    low_score = (100 - i.dcs_current) * 0.6

    return fall + due + blocked + stagnant + deps + low_score


def trend_arrow(delta: int) -> str:
    if delta > 0:
        return f"↑ +{delta}"
    if delta < 0:
        return f"↓ {delta}"
    return "→ 0"


def decision_prompt(i: Initiative) -> str:
    """
    Lightweight decision-category suggestion based on drivers.
    """
    prompts = []

    if i.scope_changes_14d >= 2:
        prompts.append("Freeze scope / lock acceptance criteria")
    if i.blocked_days >= 2 or i.days_stagnant >= 4:
        prompts.append("Remove blocker or re-route critical path")
    if i.critical_dependency or i.dependency_count >= 4:
        prompts.append("Escalate dependency alignment / sequence work")
    if i.days_to_target <= 14 and i.dcs_current < 80:
        prompts.append("Decide: add capacity vs reduce deliverable surface area vs accept slip")

    if not prompts:
        prompts.append("Continue current plan; monitor trend")

    # Keep it short
    return "; ".join(prompts[:2])


def render_brief(portfolio_meta: Dict[str, Any], initiatives: List[Initiative]) -> str:
    week_ending = portfolio_meta.get("week_ending", datetime.utcnow().strftime("%Y-%m-%d"))
    counts = band_counts(initiatives)

    # Biggest movers
    biggest_drop = min(initiatives, key=lambda x: x.delta)
    biggest_gain = max(initiatives, key=lambda x: x.delta)

    # Risks: take top 3 by heuristic
    risks = sorted(initiatives, key=risk_rank, reverse=True)[:3]

    # Positives: initiatives with upward movement or strong green
    positives = sorted(
        [i for i in initiatives if i.delta > 0 or (i.band == "Green" and i.dcs_current >= 85)],
        key=lambda x: (x.delta, x.dcs_current),
        reverse=True
    )[:3]

    lines: List[str] = []
    lines.append(f"# Weekly Executive Brief — Week Ending {week_ending}")
    lines.append("")
    lines.append("## Portfolio Snapshot")
    lines.append(f"- Total initiatives: **{len(initiatives)}**")
    lines.append(f"- Confidence bands: **Green {counts.get('Green',0)}** / **Yellow {counts.get('Yellow',0)}** / **Red {counts.get('Red',0)}**")
    lines.append(f"- Largest decline: **{biggest_drop.name}** ({biggest_drop.band}, {biggest_drop.dcs_current} {trend_arrow(biggest_drop.delta)})")
    lines.append(f"- Largest improvement: **{biggest_gain.name}** ({biggest_gain.band}, {biggest_gain.dcs_current} {trend_arrow(biggest_gain.delta)})")
    lines.append("")

    lines.append("## Top Emerging Risks (Decision-Oriented)")
    for i in risks:
        drivers = []
        if i.blocked_days >= 2:
            drivers.append(f"blocked {i.blocked_days}d")
        if i.scope_changes_14d >= 2:
            drivers.append(f"scope changes {i.scope_changes_14d}/14d")
        if i.days_stagnant >= 4:
            drivers.append(f"stagnant {i.days_stagnant}d")
        if i.dependency_count >= 4 or i.critical_dependency:
            drivers.append(f"deps {i.dependency_count}" + (" (critical)" if i.critical_dependency else ""))

        driver_str = ", ".join(drivers) if drivers else "signal review needed"
        lines.append(f"- **{i.name}** — {i.band} (**{i.dcs_current} {trend_arrow(i.delta)}**) | Drivers: {driver_str} | Target: {i.days_to_target}d")
        lines.append(f"  - Decision prompt: *{decision_prompt(i)}*")
        if i.status_notes:
            lines.append(f"  - Context: {i.status_notes[0]}")
    lines.append("")

    lines.append("## Notable Positive Momentum")
    if positives:
        for i in positives:
            lines.append(f"- **{i.name}** — {i.band} (**{i.dcs_current} {trend_arrow(i.delta)}**) | Target: {i.days_to_target}d")
    else:
        lines.append("- No significant positive movement this week; focus on stabilizing top risks.")
    lines.append("")

    lines.append("## Decision Prompts Summary")
    lines.append("- Scope: Where volatility is increasing, decide whether to freeze scope or re-baseline commitments.")
    lines.append("- Dependencies: For critical path dependencies, align sequencing and escalation paths explicitly.")
    lines.append("- Capacity: For near-term targets with declining confidence, choose: add capacity vs reduce surface area vs accept slip.")
    lines.append("")

    lines.append("> Note: This brief is derived from scored operational signals. Root-cause validation may require qualitative follow-up with owners.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate an executive brief from a weekly snapshot JSON.")
    parser.add_argument("--input", required=True, help="Path to snapshot JSON (scored dataset).")
    parser.add_argument("--output", required=True, help="Path to write Markdown executive brief.")
    args = parser.parse_args()

    portfolio_meta, initiatives = load_snapshot(args.input)
    brief = render_brief(portfolio_meta, initiatives)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(brief)

    print(f"✅ Wrote executive brief to: {args.output}")


if __name__ == "__main__":
    main()
