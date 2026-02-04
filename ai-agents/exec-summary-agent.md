# Executive Summary Agent

## Purpose

The Executive Summary Agent converts structured delivery intelligence into a concise, decision-oriented weekly briefing for senior leadership.

It does not replace dashboards.
It does not restate ticket activity.
It translates signal into strategic clarity.

---

## Operating Position

This agent sits **after**:

- Hierarchy normalization
- Delivery Confidence Scoring
- Risk signal derivation
- Trend calculations

It consumes scored and structured data only.

---

## Inputs

Structured dataset snapshot (weekly):

Per Initiative:
- Delivery Confidence Score (current + prior week)
- Confidence band (Green / Yellow / Red)
- Score delta (trend)
- Blocked duration
- Scope volatility index
- Aging WIP indicator
- Dependency density
- Due date proximity
- Key status notes (curated text field)

Optional:
- Portfolio-level rollup metrics
- Cross-team risk clusters
- Resource load variance

---

## Output Format (1-Page Executive Brief)

### Section 1 — Portfolio Snapshot
- Total initiatives
- Count by confidence band
- Week-over-week movement
- Highest declining score
- Highest improving score

### Section 2 — Top Emerging Risks
Ranked by:
- Score delta magnitude
- Combined volatility + blocked duration
- Near-term due date proximity

Each risk formatted as:
- Initiative name
- Current score + trend
- Primary driver(s)
- Business impact framing
- Required decision category

### Section 3 — Notable Positive Momentum
- Initiatives recovering from Yellow → Green
- Volatility stabilized
- Blockers resolved
- Throughput improvement signals

### Section 4 — Decision Prompts
Explicit decision framing, not vague recommendations:

Examples:
- Freeze scope?
- Add temporary capacity?
- Reprioritize dependency?
- Accept timeline slip?
- Reduce deliverable surface area?

The agent should never assign ownership.
It should propose decision categories.

---

## Prompt Architecture (Version-Controlled)

### System Instruction (example)

"You are an executive operations analyst. Interpret structured delivery metrics and produce a concise, decision-oriented weekly briefing. Prioritize risk signals, trend changes, and trade-off framing. Avoid generic summaries."

---

### Structured Data Template (example input)

Initiative: Platform Modernization  
DCS: 72 (↓ -8 WoW)  
Blocked Duration: 3 days  
Scope Changes (14d): 2  
Dependencies: 4 (1 critical)  
Days to Target: 12  
Aging WIP: Moderate  

Status Notes:  
- Integration API instability impacting testing  
- New reporting requirement added  

---

### Expected Output Pattern (example)

**Platform Modernization — Yellow (72, ↓ -8)**  
Confidence declined due to renewed scope volatility and dependency friction on a critical integration API. With 12 days to target and continued scope expansion, delivery risk is increasing.  

Decision Prompt: Freeze additional reporting scope or allocate temporary integration support to stabilize trajectory.

---

## Design Constraints

The agent must:

- Be deterministic in structure
- Be consistent in tone
- Avoid speculation beyond metrics
- Avoid unnecessary verbosity
- Avoid technical jargon unless business-relevant

Max length target:
~500–700 words total.

---

## Cadence

- Run weekly (e.g., Friday morning snapshot)
- Use consistent data cutoff time
- Archive outputs in versioned Notion database or repository folder

Optional:
Maintain historical executive briefs to track narrative evolution.

---

## Guardrails

AI cannot:
- Modify source data
- Override confidence score
- Assign commitments
- Infer causation without signal support

If signal strength is weak, the agent should state:

"Confidence shift observed; root cause requires qualitative validation."

---

## Strategic Value

Traditional reporting answers:
"What happened?"

The Executive Summary Agent answers:
"What is changing, why it matters, and what decision is required?"

It converts telemetry into executive leverage.

---

## Future Enhancements

- Confidence trajectory forecasting (light regression)
- Cross-initiative dependency clustering detection
- Portfolio-level risk heatmap
- Executive Q&A simulation agent
- Automated boar
