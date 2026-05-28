# Product Brief: Marketing Performance Intelligence Tool
**Codename:** MarketPulse  
**Version:** v1 Scope  
**Author:** Assessment Submission  
**Status:** Scoped, Not Built

---

## The Problem

The team answers the same question repeatedly — *"How is our marketing performing across channels right now, and where should we focus?"* — through a process that is manual, inconsistent, and person-dependent.

**Consequences of the current state:**
- The answer varies depending on who pulls it
- It takes longer than it should (estimated 30–90 min per request)
- If the usual person is unavailable, the question goes unanswered
- There is no audit trail — you can't see what yesterday's answer was

This is not a data problem. The data exists. It's a **workflow and access problem**.

---

## Primary User

**The internal analyst / account manager** — not the client.

This is a deliberate scoping call. Designing for clients first means building auth layers, whitelabelled views, polished UI, and multi-tenant data isolation. That's a v2 problem. In v1, the most pressing pain is internal: the person who fields the question and has to go find the answer manually.

Once the internal user can answer the question in under 2 minutes consistently, we can decide whether and how to expose that to clients.

> If we designed for both simultaneously, we'd end up building neither well.

---

## What the Tool Is

A **single-page internal dashboard** that surfaces a standardised, always-current view of marketing performance across channels for any given client brand.

It answers exactly this: *"How is [Brand X] performing this week across channels, and what stands out?"*

It is **not** a reporting tool. It is a **situational awareness tool** — the difference being that a report is produced on demand, while situational awareness is always available.

---

## What Success Looks Like

A team member opens the tool, selects a brand, and within 30 seconds can answer:

1. Which channels are driving performance this week vs last?
2. Are there any channels significantly over- or under-performing relative to the recent trend?
3. Is there a clear "focus here" signal for the next conversation with the client?

They walk away with a **shared, defensible answer** — not a personal interpretation of raw data.

---

## v1 Scope

### In Scope

| Feature | Rationale |
|---|---|
| Brand selector (dropdown) | Multi-client context is the core use case |
| Channel-level performance summary (last 7 days) | "Right now" = recent window, not real-time |
| Week-over-week delta for each channel | The simplest useful trend signal |
| A single "highlight" per brand — the biggest mover | Answers "where should we focus" directly |
| Last-refreshed timestamp on all data | Builds trust; users know what they're looking at |
| Static data snapshot (manual or scheduled refresh) | Start with reliability over live connection |

### Not In Scope for v1

| Feature | Why Excluded |
|---|---|
| Client-facing view | Requires auth, whitelabelling, and trust that v1 data isn't ready for |
| Real-time / live API connections | Reliability risk; start with a known-good snapshot |
| Recommendations engine / AI suggestions | The dashboard surfacing the signal is the value; interpreting it is still the analyst's job |
| Historical trend charts (>4 weeks) | Adds complexity without changing the "right now" answer |
| Multi-brand comparison view | Useful later; not the primary question |
| Alerting / notifications | Requires infrastructure out of scope for v1 |
| Mobile optimisation | Internal tool; desktop-first is fine |

---

## Data Model

### What data does the tool need?

For each brand × channel × week:
- A primary performance metric (impressions, clicks, spend, conversions — depends on channel)
- The same metric for the prior week (for delta calculation)
- A "health" indicator: is this channel performing above, at, or below recent norms?

### Where does it come from?

This is the constraint: **the team is not changing their tools or workflow.** So the data has to come from wherever it already lives.

In practice, that means one of two approaches:

**Option A — Structured export (recommended for v1):**  
Each platform (Meta Ads, Google Ads, LinkedIn, etc.) can export CSVs. The pipeline reads from a shared folder (Google Drive, Dropbox, or a shared network path) that someone uploads to once a week. The tool reads that folder on load.

**Option B — Direct API connections:**  
Each ad platform has an API. More reliable, more complex, requires token management per client per platform. This is the right v2 path but introduces too many failure modes for v1.

The v1 recommendation is Option A with a documented path to Option B. One known-format CSV per channel per brand, dropped into a shared folder. The tool reads and renders it. No new infra. No workflow change. The team already exports this data; we're just standardising where it goes.

### Reliability and trust

The biggest trust risk in a tool like this is **stale data presented as current**. This is why every view must show a "data as of [date]" label. The tool should fail visibly (show a missing-data state) rather than silently (show last week's data without flagging it).

---

## Interaction Model

```
[Landing]
    └── Select Brand
            └── Dashboard View
                    ├── Channel cards (metric + WoW delta)
                    ├── "Focus here" highlight (biggest positive or negative mover)
                    └── Data freshness footer
```

No login required in v1 (internal tool, intranet or shared access).  
No write actions — read-only.  
No configuration UI — admin changes happen in the data files.

---

## What Would Make Users Trust It

1. **Visible data freshness** — always show when data was last updated
2. **Explicit missing-data states** — if a channel has no data, say so rather than showing zero
3. **Consistent metric definitions** — same formula every time, documented somewhere visible
4. **It matches what they'd find manually** — the first few uses need to be verified by someone who can cross-check against the source tools

---

## Technical Constraints

- Must work within existing tooling (no new SaaS purchases)
- Data source: CSV exports from existing platforms → shared folder
- No new auth system required
- Deployable as a static web app or internal hosted page (simple Python/Flask server would work)
- No database required in v1 — read directly from CSVs on load

---

## What I'd Revisit With More Time

1. **User interviews** — I've assumed the analyst is the primary user. A single 30-minute conversation with two or three people who currently answer this question would sharpen or invalidate that assumption entirely.

2. **Metric definitions** — "performance" means different things per channel. I've left this abstract. In a real scoping, I'd force a decision: what is the one number that matters per channel?

3. **The "focus here" logic** — I've described it as "biggest mover." That could be the wrong signal. A channel that's always volatile looks like a big mover even when nothing is wrong. Normalising by channel baseline would be better but adds complexity.

4. **CSV schema standardisation** — Option A only works if everyone exports in the same format. That's an ops problem as much as a technical one, and I've assumed it away here.

5. **Path to v2** — I'd want to map the API connection work explicitly so v2 isn't a rewrite of v1 but a layer added on top.
