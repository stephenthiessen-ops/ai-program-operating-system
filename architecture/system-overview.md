# System Architecture — AI Program Operating System

## Purpose
This architecture converts operational execution data into decision-ready intelligence using a repeatable, auditable pipeline. The intent is to reduce manual scanning, surface risk earlier, and create a consistent narrative from delivery → strategy.

---

## Architecture Layers

### 1) Source Systems (Execution + Signals)
These systems generate the raw operational telemetry.

- **Work system:** Jira (issues, status, ownership, estimates, due dates, dependencies)
- **Code system:** GitHub (PRs, commits, releases, workflow runs)
- **Knowledge system:** Notion (program wiki, decision logs, risk registers)
- **Optional inputs:** Slack/Email/Docs exports (signals, blockers, stakeholder asks)

**Output:** semi-structured records (tickets, events, timestamps, text fields)

---

### 2) Ingestion & Normalization (Data Layer)
The pipeline extracts and standardizes records into a consistent schema.

Key activities:
- Normalize issue hierarchies (Sub-task → Story → Epic → Initiative)
- Standardize statuses into canonical states (e.g., Not Started / In Progress / Blocked / Done)
- Clean ownership fields and team mappings
- Generate time-series events from change logs (status transitions, scope changes)

**Output:** structured dataset with stable identifiers + time-based history

---

### 3) Scoring & Derived Metrics (Operational Intelligence)
The system enriches the dataset with derived indicators.

Examples:
- **Delivery Confidence Score** (probabilistic/heuristic likelihood of meeting target)
- **Scope Volatility Index** (change-rate of points, requirements, or acceptance criteria)
- **Flow Efficiency** (active time vs waiting time proxies)
- **Risk Signals** (blocked duration, dependency density, aging WIP, SLA misses)

**Output:** metrics table + scored entities (initiative/epic/story)

---

### 4) AI Interpretation (Narrative + Recommendations)
AI is used on top of structured data to convert signals into a usable weekly/biweekly narrative.

Typical outputs:
- Executive summary (what changed, why it matters, what needs a decision)
- Risks & mitigations (ranked by impact/likelihood)
- Delivery forecast narrative (confidence drivers + detractors)
- Decision prompts (trade-offs, resourcing asks, scope decisions)

**Important constraint:** AI should not be the system of record.
It should interpret the system of record.

---

### 5) Publishing & Feedback Loop (Decision Layer)
Outputs are distributed back into the working cadence.

Destinations:
- Notion (weekly brief, decision log, program page updates)
- Dashboards/BI (confidence trend, risk heatmap, scope volatility)
- Optional: Jira comments or issue fields (light-touch enrichment)

**End Result:** a closed loop where execution data becomes a stable, repeatable input to strategic decision-making.

---

## Operational Principles
- **Auditability:** every output should trace back to an input record and a deterministic transformation step
- **Repeatability:** same inputs + same config → same outputs (versioned in GitHub)
- **Minimal friction:** automate collection; keep humans focused on judgment and decisions
- **Signal > noise:** prioritize early indicators (risk, drift, dependencies) over raw activity counts

---

## Data Contracts (High-Level)
Entities:
- Initiative (portfolio-level outcome)
- Epic (value stream / deliverable grouping)
- Story (unit of delivery)
- Sub-task (execution detail)

Core fields:
- ID, title, owner, team
- status (canonical), target date, created date
- estimate (points/time), remaining work proxy
- blocked flag + blocked duration
- dependency count + dependency criticality
- scope change events (count + magnitude)
