# AI Layer Model — Role, Constraints, and Guardrails

## Purpose
Define exactly where AI operates within the AI Program Operating System — and where it does not.

AI augments interpretation.
It does not replace structured data, ownership, or decision authority.

---

## AI Layer Responsibilities

AI operates **after structured scoring and signal detection**.

It performs:

1. **Narrative Synthesis**
   - Convert scored metrics into executive-readable summaries
   - Highlight key changes week-over-week
   - Identify emerging patterns

2. **Risk Framing**
   - Translate risk signals into business impact language
   - Propose mitigation categories (not prescriptive solutions)

3. **Trend Interpretation**
   - Detect acceleration/decay in delivery confidence
   - Identify systemic patterns (recurring blockers, scope churn)

4. **Decision Prompting**
   - Surface trade-offs
   - Suggest decision categories (rescope / resource / defer)

---

## What AI Must NOT Do

AI is explicitly constrained from:

- Acting as the system of record
- Modifying Jira data autonomously
- Assigning ownership
- Making delivery commitments
- Generating confidence scores directly
- Overriding deterministic scoring logic

All scoring must be derived from rule-based, version-controlled logic.

AI interprets.
It does not compute foundational truth.

---

## Data Boundary Model

AI input should only include:

- Structured scored dataset
- Derived metrics (DCS, volatility, aging WIP)
- Historical trend deltas
- Relevant qualitative summaries (status notes)

AI should not receive:
- Raw unstructured logs
- PII
- Sensitive security content
- Unbounded conversation transcripts

This ensures:
- Predictable output
- Reduced hallucination risk
- Auditability

---

## Audit & Reproducibility

Every AI output must:
- Be generated from a versioned prompt
- Reference timestamped dataset
- Be reproducible from the same input snapshot

Recommended structure:

/ai-agents
   /prompts
   /templates
   /versions

This allows inspection of:
- Prompt evolution
- Output drift
- Model changes

---

## Operating Principle

Deterministic logic creates the signal.
AI translates the signal into insight.

Without deterministic scoring, AI becomes speculative.
With scoring, AI becomes strategic amplification.

---

## Strategic Positioning

In this model:

Human judgment owns:
- Decisions
- Trade-offs
- Commitments
- Resource allocation

AI owns:
- Pattern synthesis
- Signal summarization
- Narrative acceleration
- Cognitive load reduction

This preserves accountability while increasing clarity and velocity.
