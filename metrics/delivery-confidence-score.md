# Delivery Confidence Score (DCS)

## What it is
A practical scoring model that estimates the likelihood a delivery item (Initiative/Epic/Story) will meet its target date or committed scope, using observable operational signals.

This is not a promise.
It’s an early-warning system.

---

## Outputs
- **Score (0–100):** higher = more likely to deliver as planned
- **Band:** Green / Yellow / Red
- **Drivers:** top positive/negative contributors
- **Trend:** week-over-week direction (↑ / ↓ / →)

---

## Scoring Strategy
The score begins at 100 and subtracts weighted penalties for risk signals. Bonuses can be added for stabilizing indicators.

### A) Core Risk Penalties (subtract)
1) **Blocked Time Penalty**
- If blocked_duration_days > threshold:
  - penalty = min(25, blocked_duration_days * 5)

2) **Scope Volatility Penalty**
- scope_change_events_last_14d:
  - penalty = min(20, scope_change_events * 4)

3) **Aging WIP Penalty**
- days_in_progress_without_movement:
  - penalty = min(20, days_stagnant * 3)

4) **Dependency Density Penalty**
- dependency_count:
  - penalty = min(15, dependency_count * 3)
- optional: add +5 if dependency is “critical path”

5) **Owner/Team Instability Penalty**
- owner_changes_last_30d:
  - penalty = min(10, owner_changes * 5)

6) **Due Date Proximity Penalty**
- days_to_target:
  - if days_to_target <= 7 and status not near-done → penalty = 15
  - if days_to_target <= 14 and significant work remains → penalty = 10

---

### B) Stabilizing Bonuses (add)
1) **Recent Throughput Bonus**
- meaningful_status_progress_last_7d = true → +5

2) **Low WIP Bonus**
- team_wip_under_limit = true → +5

3) **Stable Scope Bonus**
- scope_change_events_last_14d == 0 → +5

Cap total bonuses at **+10** to prevent masking risk.

---

## Final Score
