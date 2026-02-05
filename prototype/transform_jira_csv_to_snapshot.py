#!/usr/bin/env python3
"""
Transform a Jira-export-style CSV into the snapshot JSON format consumed by generate_exec_brief.py.

Design goals:
- Works with a lightweight CSV schema (no Jira API needed)
- Normalizes hierarchy: Initiative -> Epic -> Story (sub-tasks optional)
- Aggregates signals to initiative-level
- Produces deterministic outputs suitable for portfolio use

Run:
  python prototype/transform_jira_csv_to_snapshot.py \
    --input prototype/jira_export_SAMPLE.csv \
    --output prototype/snapshot_from_csv.json \
    --week-ending 2026-02-06
"""

from __future__ import annotations
import csv
import json
import argparse
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple


REQUIRED_HEADERS = [
    "Issue key",
    "Issue Type",
    "Summary",
    "Status",
    "Parent key",
]

OPTIONAL_HEADERS_DEFAULTS = {
    "Story Points": "",
    "Assignee": "",
    "Updated": "",
    "Due date": "",
    "Blocks": "0",
    "Blocked Days": "0",
    "Scope Changes (14d)": "0",
}


def parse_int(x: str, default: int = 0) -> int:
    try:
        x = (x or "").strip()
        if x == "":
            return default
        # handle "5.0" etc
        return int(float(x))
    except Exception:
        return default


def parse_date(x: str) -> Optional[date]:
    x = (x or "").strip()
    if not x:
        return None
    # common Jira exports: YYYY-MM-DD or MM/DD/YYYY
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(x, fmt).date()
        except ValueError:
            continue
    return None


def normalize_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s in ("done", "closed", "resolved"):
        return "Done"
    if s in ("blocked",):
        return "Blocked"
    if s in ("in progress", "in-progress", "inprogress", "doing"):
        return "In Progress"
    if s in ("to do", "todo", "backlog", "not started", "open"):
        return "Not Started"
    # passthrough with title-case
    return status.strip() or "Unknown"


@dataclass
class Row:
    key: str
    issue_type: str
    summary: str
    status: str
    parent_key: str
    story_points: int = 0
    assignee: str = ""
    updated: str = ""
    due_date: Optional[date] = None
    blocks: int = 0
    blocked_days: int = 0
    scope_changes_14d: int = 0


@dataclass
class InitiativeAgg:
    id: str
    name: str
    # Derived / aggregated signals:
    total_points: int = 0
    done_points: int = 0
    blocked_days: int = 0
    scope_changes_14d: int = 0
    dependency_count: int = 0
    critical_dependency: bool = False
    days_stagnant: int = 0  # proxy derived from status mix, kept simple here
    due_date: Optional[date] = None
    status_notes: List[str] = field(default_factory=list)


def load_csv(path: str) -> List[Row]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV has no headers.")

        missing = [h for h in REQUIRED_HEADERS if h not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required headers: {missing}")

        # fill optional headers if absent
        for h, _default in OPTIONAL_HEADERS_DEFAULTS.items():
            if h not in reader.fieldnames:
                # DictReader won't produce them; handle via get()
                pass

        rows: List[Row] = []
        for r in reader:
            key = (r.get("Issue key") or "").strip()
            if not key:
                continue

            rows.append(
                Row(
                    key=key,
                    issue_type=(r.get("Issue Type") or "").strip(),
                    summary=(r.get("Summary") or "").strip(),
                    status=normalize_status(r.get("Status") or ""),
                    parent_key=(r.get("Parent key") or "").strip(),
                    story_points=parse_int(r.get("Story Points", OPTIONAL_HEADERS_DEFAULTS["Story Points"])),
                    assignee=(r.get("Assignee", OPTIONAL_HEADERS_DEFAULTS["Assignee"]) or "").strip(),
                    updated=(r.get("Updated", OPTIONAL_HEADERS_DEFAULTS["Updated"]) or "").strip(),
                    due_date=parse_date(r.get("Due date", OPTIONAL_HEADERS_DEFAULTS["Due date"]) or ""),
                    blocks=parse_int(r.get("Blocks", OPTIONAL_HEADERS_DEFAULTS["Blocks"])),
                    blocked_days=parse_int(r.get("Blocked Days", OPTIONAL_HEADERS_DEFAULTS["Blocked Days"])),
                    scope_changes_14d=parse_int(r.get("Scope Changes (14d)", OPTIONAL_HEADERS_DEFAULTS["Scope Changes (14d)"])),
                )
            )
        return rows


def build_parent_map(rows: List[Row]) -> Dict[str, str]:
    """
    child_key -> parent_key (if provided)
    """
    m: Dict[str, str] = {}
    for r in rows:
        if r.parent_key:
            m[r.key] = r.parent_key
    return m


def index_rows(rows: List[Row]) -> Dict[str, Row]:
    return {r.key: r for r in rows}


def find_initiative_key(issue_key: str, parent_map: Dict[str, str], row_index: Dict[str, Row]) -> Optional[str]:
    """
    Walk up Parent key pointers until we find an Initiative.
    """
    cur = issue_key
    visited = set()
    for _ in range(20):  # safety
        if cur in visited:
            return None
        visited.add(cur)

        row = row_index.get(cur)
        if row and row.issue_type.lower() == "initiative":
            return row.key

        parent = parent_map.get(cur)
        if not parent:
            return None
        cur = parent
    return None


def dcs_from_signals(
    pct_done: float,
    blocked_days: int,
    scope_changes_14d: int,
    dependency_count: int,
    critical_dependency: bool,
    days_to_target: Optional[int],
    has_blocked_items: bool,
) -> int:
    """
    Deterministic heuristic score. This aligns with your DCS doc, but simplified for a CSV demo.
    """
    score = 100

    # progress anchoring (more done == more confidence)
    # maps 0..1 -> penalty 30..0
    score -= int((1.0 - max(0.0, min(1.0, pct_done))) * 30)

    # blocked time
    score -= min(25, blocked_days * 5)

    # scope volatility
    score -= min(20, scope_changes_14d * 4)

    # dependencies
    dep_pen = min(15, dependency_count * 3) + (5 if critical_dependency else 0)
    score -= dep_pen

    # due-date proximity pressure
    if days_to_target is not None:
        if days_to_target <= 7 and pct_done < 0.8:
            score -= 15
        elif days_to_target <= 14 and pct_done < 0.6:
            score -= 10

    # extra penalty if anything is currently blocked
    if has_blocked_items:
        score -= 8

    return max(0, min(100, score))


def band_from_dcs(dcs: int) -> str:
    if dcs >= 80:
        return "Green"
    if dcs >= 60:
        return "Yellow"
    return "Red"


def transform(rows: List[Row], week_ending: str) -> Dict:
    parent_map = build_parent_map(rows)
    row_index = index_rows(rows)

    # Identify initiatives present
    initiatives_rows = [r for r in rows if r.issue_type.lower() == "initiative"]
    initiatives: Dict[str, InitiativeAgg] = {}
    for r in initiatives_rows:
        initiatives[r.key] = InitiativeAgg(id=r.key, name=r.summary, due_date=r.due_date)

    # Aggregate children up to initiatives
    for r in rows:
        ikey = find_initiative_key(r.key, parent_map, row_index)
        if not ikey:
            continue
        if ikey not in initiatives:
            # initiative row missing; create placeholder
            initiatives[ikey] = InitiativeAgg(id=ikey, name=f"{ikey} (unresolved title)")

        agg = initiatives[ikey]

        # Due date: choose earliest due date we can find (initiative-level target)
        if r.due_date:
            if agg.due_date is None or r.due_date < agg.due_date:
                agg.due_date = r.due_date

        # Only use points from Stories/Sub-tasks for progress proxy
        if r.issue_type.lower() in ("story", "sub-task", "subtask", "task"):
            pts = r.story_points
            agg.total_points += pts
            if r.status == "Done":
                agg.done_points += pts

        agg.blocked_days = max(agg.blocked_days, r.blocked_days)  # max as “worst observed”
        agg.scope_changes_14d += r.scope_changes_14d
        agg.dependency_count += r.blocks
        if r.blocks >= 3:
            agg.critical_dependency = True

        # Capture lightweight notes
        if r.status == "Blocked" and r.summary:
            agg.status_notes.append(f"Blocked: {r.summary}")
        elif r.issue_type.lower() == "initiative" and r.summary:
            # avoid adding initiative title as a note
            pass

    # Compute days_to_target based on week ending
    we = parse_date(week_ending)
    if not we:
        raise ValueError("week_ending must be a date like YYYY-MM-DD")

    out_inits = []
    for agg in initiatives.values():
        pct_done = (agg.done_points / agg.total_points) if agg.total_points > 0 else 0.0

        days_to_target = None
        if agg.due_date:
            days_to_target = (agg.due_date - we).days

        # detect any blocked items under this initiative
        has_blocked_items = any(n.startswith("Blocked:") for n in agg.status_notes)

        dcs_current = dcs_from_signals(
            pct_done=pct_done,
            blocked_days=agg.blocked_days,
            scope_changes_14d=agg.scope_changes_14d,
            dependency_count=agg.dependency_count,
            critical_dependency=agg.critical_dependency,
            days_to_target=days_to_target,
            has_blocked_items=has_blocked_items,
        )

        # For demo purposes: set prior as current +/- small deterministic drift based on volatility
        drift = min(8, agg.scope_changes_14d * 2 + (2 if has_blocked_items else 0))
        dcs_prior = max(0, min(100, dcs_current + drift))  # slightly “better last week” if volatility exists

        band = band_from_dcs(dcs_current)

        # days_stagnant proxy: if little done and close to due, treat as stagnant
        if agg.total_points > 0 and pct_done < 0.3 and (days_to_target is not None and days_to_target <= 14):
            agg.days_stagnant = 4
        else:
            agg.days_stagnant = 1 if pct_done < 0.8 else 0

        # Notes: keep very short; cap to 2 lines
        notes = agg.status_notes[:2]
        if not notes:
            notes = ["No significant blockers detected in snapshot."]

        out_inits.append(
            {
                "id": agg.id,
                "name": agg.name,
                "dcs_current": int(dcs_current),
                "dcs_prior": int(dcs_prior),
                "band": band,
                "blocked_days": int(agg.blocked_days),
                "scope_changes_14d": int(agg.scope_changes_14d),
                "days_stagnant": int(agg.days_stagnant),
                "dependency_count": int(agg.dependency_count),
                "critical_dependency": bool(agg.critical_dependency),
                "days_to_target": int(days_to_target) if days_to_target is not None else 21,
                "status_notes": notes,
            }
        )

    # stable ordering: worst confidence first to make diffs meaningful
    out_inits.sort(key=lambda x: (x["band"], x["dcs_current"]))

    return {
        "portfolio": {
            "week_ending": week_ending,
            "total_initiatives": len(out_inits),
            "source": "csv_transform",
        },
        "initiatives": out_inits,
    }


def main():
    parser = argparse.ArgumentParser(description="Transform Jira CSV export into snapshot JSON.")
    parser.add_argument("--input", required=True, help="Path to input CSV.")
    parser.add_argument("--output", required=True, help="Path to output snapshot JSON.")
    parser.add_argument("--week-ending", required=True, help="Week ending date (YYYY-MM-DD).")
    args = parser.parse_args()

    rows = load_csv(args.input)
    snapshot = transform(rows, args.week_ending)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"✅ Wrote snapshot to: {args.output}")


if __name__ == "__main__":
    main()
