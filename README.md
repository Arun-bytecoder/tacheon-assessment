# Tacheon Assessment — Data & AI Product Engineer

**Candidate:** Arunachalam
**Submitted:** May 2026
**GitHub:** [github.com/Arun-bytecoder/tacheon-assessment](https://github.com/Arun-bytecoder/tacheon-assessment)

---

## Repository Structure

```
tacheon-assessment/
├── task-1-product-scoping/    # Product scoping — MarketPulse internal tool
│   ├── README.md
│   ├── Productbrief.md
│   ├── FlowDiagram.md
│   └── Wireframe.html
│
├── task-2-pipeline/           # Python data pipeline — Open-Meteo → BigQuery
│   ├── README.md
│   ├── pipeline.py
│   ├── test_pipeline.py
│   ├── requirements.txt
│   └── sql/
│       └── summary_queries.sql
│
├── .gitignore
└── README.md                
```

---

## Task 1 — Product Scoping

The scenario asked how a marketing technology team could answer the recurring question — *"How is our marketing performing across channels right now, and where should we focus?"* — faster, more consistently, and without depending on one person.

I scoped an internal tool called **MarketPulse**. The brief covers:
- Why the primary user is the internal analyst, not the client
- What V1 does and deliberately does not do
- Where the data comes from without changing existing team workflows
- What makes users trust the output
- A flow diagram covering user flow, data flow, and V1 vs V2 boundary
- An interactive wireframe showing the dashboard layout

See [`task-1-product-scoping/README.md`](task-1-product-scoping/README.md) for full details.

---

## Task 2 — Data Pipeline

I built a Python pipeline that fetches hourly weather data from the Open-Meteo API, transforms it into an analytics-ready table with derived fields, and loads it into Google BigQuery.

Key highlights:
- 504 rows loaded — 3 cities × 168 hourly records over 7 days
- 6 derived fields added beyond raw API data
- Graceful error handling — one city failing does not stop the rest
- Explicit BigQuery schema — no type inference
- 5 SQL summary queries verified against real data
- 13 unit tests — all passing
- Production thinking documented — scheduling, failure detection, scaling

See [`task-2-pipeline/README.md`](task-2-pipeline/README.md) for full details.

---
