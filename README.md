# Tacheon Assessment — Data & AI Product Engineer

**Candidate:** Arunachalam  
**Submitted:** 28th May 2026  
**Repo:** [github.com/Arun-bytecoder/tacheon-assessment](https://github.com/Arun-bytecoder/tacheon-assessment)

---

## Repository Structure

```
tacheon-assessment/
├── task-1-product-scoping/   # Product scoping document and wireframes
└── task-2-pipeline/          # Python data pipeline: Open-Meteo → BigQuery
```

---

## Task 1: Product Scoping

A scoping document for an internal marketing performance tool. Covers:
- Problem definition and primary user
- V1 scope and deliberate exclusions
- Data sources and system flow
- Trust and consistency considerations

See [`task-1-product-scoping/README.md`](task-1-product-scoping/README.md) for full details.

---

## Task 2: Data Pipeline

A working Python pipeline that fetches hourly weather data from Open-Meteo, transforms it with derived analytical fields, and loads it into Google BigQuery.

- 504 rows loaded across 3 cities (London, New York, Tokyo)
- 6 derived fields added beyond raw API data
- 5 SQL summary queries included
- Production thinking documented in README

See [`task-2-pipeline/README.md`](task-2-pipeline/README.md) for full details.

---
