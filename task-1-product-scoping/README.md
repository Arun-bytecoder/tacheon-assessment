# Task 1: Product Scoping

**Status**: Complete 
**Last Updated**: May 27, 2026

## Quick Summary

I'm scoping **Marketing Performance Dashboard**: an internal tool that aggregates performance data across marketing channels and displays it in a single view. It replaces a manual 30-minute reporting process with a 5-minute lookup.

**Primary user**: Internal analyst  
**V1 scope**: 4 channels (Google Ads, Facebook, Email, Organic), weekly refresh, performance summary + ROI ranking  
**Approach**: Manual CSV upload (team doesn't change workflow), simple dashboard interface

---

## Documentation

This folder contains:

1. **`01-research-notes.md`** - My research thinking
   - User analysis: Who benefits most from this tool?
   - Data flow: Where does data come from, how does it move?
   - Key assumptions I'm making
   - Decisions and reasoning

2. **`02-product-brief.md`** - Complete product specification
   - Executive summary of the problem and solution
   - User flows and success criteria
   - V1 scope (what's in) and out-of-scope (what's not, with reasoning)
   - Wireframe/interface design
   - Data quality mechanisms and trust-building strategies
   - Metrics for success
   - Open questions to validate

3. **Wireframe mockup** - Dashboard interface design
   - Shows exactly what the user sees
   - Performance summary at a glance
   - Channel-by-channel breakdown
   - "Where to focus" ranking based on ROI

---

## The Problem

**Current state**: Team spends 30+ minutes manually answering "How is our marketing performing across channels?"
- Someone logs into Google Ads, pulls data
- Logs into Facebook Ads, pulls data
- Checks analytics platform
- Stitches together a response
- Answer looks different every time

**Why this is a problem**:
- Slow (30 min per request)
- Inconsistent (different answers depending on who does it)
- Single point of failure (depends on one person)
- No time for strategic thinking

---

## The Solution

**Marketing Performance Dashboard** - A single-view dashboard showing:
- Performance across 4 major marketing channels
- Key metrics: spend, conversions, revenue, ROI
- Weekly summary + trend
- Clear ranking of which channels to focus on

**Why this solves it**:
- 5-minute lookup vs 30-minute manual work
- Same answer every time (consistent)
- No single person bottleneck
- Fits around existing tools (team doesn't change workflow)

---

## V1 Scope (What's In)

✅ **Features**:
- Single dashboard view (no complex drill-downs)
- 4 channels: Google Ads, Facebook Ads, Email, Organic/Direct
- Key metrics: Spend, conversions/leads, revenue, ROI
- Weekly data (updated every Monday)
- "Where to focus" ranking (by ROI)
- Simple CSV export
- Data source attribution + refresh time (for trust)

✅ **Technology**:
- Database: SQL or Google Sheets
- Data input: Manual CSV upload (analysts export from each tool weekly)
- Dashboard: Simple web interface or tool
- Refresh: Weekly, automated

✅ **Users**: Internal analyst (primary), leadership (view-only, future)

---

## V1 Out-of-Scope (Why?)

❌ **Real-time updates**
- Why not: Adds complexity, strategic decisions happen weekly anyway
- When: Add if leadership needs intraday decisions

❌ **Client self-service portal**
- Why not: Data privacy/access complexity, internal use solves core problem first
- When: Add once internal tool is proven

❌ **Advanced drill-downs & detailed analysis**
- Why not: Overcomplicated for v1, users can dig deeper in source tools if needed
- When: Add if users request deeper investigation features

❌ **AI-powered insights / Alerts**
- Why not: Team reviews dashboards weekly, not continuous monitoring
- When: Add if monitoring becomes critical

❌ **Custom metrics per client**
- Why not: Configuration burden, adds complexity
- When: Standardize common templates in v2

❌ **Predictive/forecasting**
- Why not: Need historical data patterns first
- When: Add in v2 after 6 months of data

❌ **Channels beyond the core 4**
- Why not: 80/20 rule - these 4 cover ~80% of marketing spend
- When: Add as other channels become significant

---

## Key Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Primary user | Internal analyst | They ask the question most, they control response, they need consistency |
| Data sources | CSV upload | Simple to implement, team doesn't change tools (constraint), proves concept |
| Channels | 4 major (Google, Facebook, Email, Organic) | 80/20 rule, good coverage, can expand later |
| Refresh cadence | Weekly | Good balance of freshness vs effort, strategic decisions are weekly anyway |
| UI approach | Dashboard summary + ranking | Quick scanning, actionable, avoids analysis paralysis |
| Client access | Not in v1 | Complexity, internal success first, then layer in client access |
| Real-time | Not in v1 | Adds complexity, weekly is fine for strategic planning |

---

## Data Flow

```
Existing Tools (team uses these)
├─ Google Ads
├─ Facebook Ads Manager
├─ Email Platform
└─ GA4

↓ (analysts export CSVs weekly)

Manual Upload Interface
↓
Data Normalization & Transformation
├─ Flatten structures
├─ Handle missing/null data
├─ Calculate ROI & efficiency metrics
└─ Attribute to source

↓

Database/Storage
↓

Dashboard View
└─ Performance summary
└─ Channel breakdown
└─ ROI ranking
```

---

## Why This Approach Works

1. **Fits the constraint**: Team continues exporting from existing tools (no change)
2. **Solves the pain**: 5-min lookup instead of 30-min manual work
3. **Builds trust**: Shows data sources, transparent calculations
4. **Simple to build**: No complex API automation or data pipelining in v1
5. **Focused scope**: Does one thing well (answer the performance question)
6. **Proves value**: Once successful, can add real-time APIs, client access, more features

---

## Assumptions I'm Making

- [ ] Analysts are OK with weekly updates (not real-time)
- [ ] Manual CSV upload is acceptable
- [ ] 4 channels sufficient for v1
- [ ] ROI is the right ranking metric
- [ ] Simple dashboard beats complex analytical tool
- [ ] Internal analysts benefit most initially

**To validate with the team:**
- Is weekly sufficient, or do you need daily updates?
- What metrics matter most to your decisions?
- Are there other channels we should prioritize?
- Who will own uploading data weekly?

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to answer question | < 5 minutes |
| Answer consistency | 100% (same numbers every time) |
| Team adoption | 80%+ use it regularly |
| Data accuracy | 99%+ (spot-checks match source) |
| User trust | High (analysts believe the numbers) |

---

## What's Next

1. **Validate assumptions** with the team (are weekly updates OK? other channels?)
2. **Design the upload interface** (how do analysts upload CSVs?)
3. **Build the database** (schema for normalized channel data)
4. **Create the dashboard** (simple web interface)
5. **Pilot with 2-3 analysts** (get feedback, iterate)
6. **Document the methodology** (how ROI is calculated, data sources, definitions)

---

## Detailed Documents

- See `01-research-notes.md` for my thinking process (user research, data flow, trust mechanisms)
- See `02-product-brief.md` for the complete product specification (wireframe, scope details, metrics, rationale)

---

## Thinking Narrative (What I Considered)

### User Choice: Why Internal Analyst?
**Options considered**:
1. Internal analyst
2. Client
3. Both

**Why analyst wins for v1**: They control the narrative for clients and leadership, they use it most frequently, and they need consistency to maintain credibility. Adding client access adds complexity (data access, privacy, configuration per client) that's better solved after the internal tool is proven and trusted.

### Data Source Strategy: Why Manual Upload?
**Options considered**:
1. Full API automation (Google Ads API, Facebook API, GA4 API)
2. Manual CSV upload
3. Hybrid (APIs for some, manual for others)

**Why manual wins for v1**: Simpler to build, the team is not changing tools (hard constraint), it doesn't require API credentials and complex error handling, and it proves the concept without technical complexity. Once the tool is trusted and used regularly, we can invest in API automation.

### Scope: Why These 4 Channels?
**Options considered**:
- 2 channels (Google & Facebook only)
- 4 channels (Google, Facebook, Email, Organic)
- 6+ channels (including LinkedIn, Display, Affiliate, etc.)

**Why 4 wins**: The 80/20 rule - these 4 typically cover 80% of marketing spend. It's comprehensive enough to be useful without being overwhelming. We can add more channels later as they become significant. Starting too broad = analysis paralysis and complexity.

### Refresh Cadence: Why Weekly?
**Options considered**:
- Real-time (live updates)
- Daily
- Weekly
- Monthly

**Why weekly wins**: Strategic decisions about where to focus happen weekly/monthly anyway, not intraday. Weekly updates are fresh enough without requiring automation complexity. Can upgrade to daily/real-time later if leadership needs intraday decisions. Avoids over-engineering for a requirement that doesn't exist yet.

### Interface: Why Dashboard vs Detailed Report?
**Options considered**:
- Detailed multi-page report (for deep analysis)
- Simple dashboard summary (for quick decisions)
- Both (dashboard + detailed reports)

**Why dashboard wins for v1**: The core question is "where should we focus?" which requires a quick answer. A dashboard summary with rankings is faster and more actionable. Analysts can drill into source tools if they need details. Simpler to build and maintain.

---

## Files in This Folder

```
task-1-product-scoping/
├── README.md (this file)
├── 01-research-notes.md (detailed thinking process)
├── 02-product-brief.md (complete product specification)
└── wireframe.png (dashboard mockup - or embedded in product brief)
```