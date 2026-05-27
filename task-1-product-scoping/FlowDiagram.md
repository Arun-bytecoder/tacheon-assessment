# Flow Diagrams

## User Flow

```
Team member opens tool
        │
        ▼
   Select brand
   [Dropdown: Brand A / Brand B / Brand C ...]
        │
        ▼
   Dashboard loads
        │
        ├──► Channel cards (one per active channel)
        │         Each shows:
        │         - Channel name (Paid Social / Paid Search / Email / Organic)
        │         - Primary metric value (this week)
        │         - WoW delta (▲ +12% / ▼ -8%)
        │         - Status indicator (On track / Watch / Underperforming)
        │
        ├──► "Focus here" highlight box
        │         - Biggest positive or negative mover this week
        │         - Plain-language label: "Paid Social is your standout this week (+23% CTR)"
        │
        └──► Data freshness footer
                  - "Data as of [date]. Next refresh: [date]."
                  - If data is missing: "No data for [channel] this week"
```

---

## Data Flow

```
Platform exports (weekly)
  Meta Ads Manager  ──► CSV export
  Google Ads        ──► CSV export       ──► Shared folder
  LinkedIn Ads      ──► CSV export           (Drive / Dropbox)
  Email platform    ──► CSV export                │
                                                   ▼
                                        Pipeline script runs
                                        (reads CSVs, validates,
                                         calculates WoW deltas,
                                         writes to /data/[brand]/)
                                                   │
                                                   ▼
                                        Dashboard app reads
                                        /data/ on page load
                                                   │
                                                   ▼
                                        User sees current view
```

---

## v1 vs v2 Boundary

```
v1 (this scope)                    v2 (next)
─────────────────────              ──────────────────────
CSV exports → shared folder   →    Live API connections
Internal users only           →    Client-facing view + auth
Manual refresh (weekly)       →    Scheduled / event-triggered
Static highlight logic        →    Configurable thresholds
Desktop web                   →    Mobile responsive
```

---

## What the Tool Deliberately Does NOT Do

```
User asks: "Why did Paid Search drop?"
    │
    └──► Tool: shows the number. Doesn't explain it.
         (That's still the analyst's job in v1)

User asks: "What should I tell the client to do?"
    │
    └──► Tool: shows the "focus here" signal.
         (Recommendation generation is v2+)

User asks: "How did we perform last quarter?"
    │
    └──► Tool: shows last 7 days and WoW delta only.
         (Historical trend is v2)
```