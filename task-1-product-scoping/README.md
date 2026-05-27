# Task 1: Product Scoping — MarketPulse

## What's in this folder

| File | What it is |
|---|---|
| `PRODUCT_BRIEF.md` | Full scoping document — the core deliverable |
| `wireframe.html` | Interactive wireframe of the v1 dashboard |
| `FLOW_DIAGRAM.md` | User flow and data flow in text/diagram form |

---

## The One-Line Answer

An internal, read-only dashboard that gives any team member a consistent, 30-second answer to *"how is [Brand X] performing this week and where should we focus?"* — pulling from CSV exports the team already produces, requiring no new tools and no workflow change.

---

## Key Decisions and Why

**Internal-first, not client-facing.**  
The loudest pain is internal. Building client-facing first means adding auth, whitelabelling, and trust infrastructure before you've validated whether the underlying data view is even right. Internal first lets you iterate fast.

**CSV ingestion, not live API connections.**  
The constraint says the team won't change their tools or workflow. They already export this data. A shared folder with standardised CSV drops is zero workflow change. Live API connections are the right v2 path but introduce token management, platform-specific rate limits, and per-client credential handling — too much failure surface for v1.

**No AI/recommendations in v1.**  
The question is "how are we performing and where should we focus?" Surfacing the signal (biggest mover, WoW delta) answers the "focus" question without needing a model. Adding an LLM layer before the data plumbing is solid is backwards.

**One highlight per brand ("Focus here").**  
Every dashboard risks becoming a place where information goes to be ignored. Forcing a single "focus here" signal — the biggest mover across channels — means someone always walks away with an action, not just a view.

---

## What I'd Revisit

- Actual metric definitions per channel (I've left these abstract — a real scoping needs a decision here)
- Whether "biggest mover" is the right signal for the highlight, or whether it should be normalised against channel baseline volatility
- User interviews to validate the analyst-as-primary-user assumption
- CSV schema standardisation — technically simple, operationally non-trivial

---

## What I'd Build Next (v2 Signals)

1. Direct API connectors per platform (Meta, Google, LinkedIn) — replaces the CSV folder
2. Client-facing view with auth and brand-level access control
3. Trend sparklines (4-week view) — the "right now" question eventually needs "compared to when?"
4. Alerting: ping Slack when a channel drops >X% WoW