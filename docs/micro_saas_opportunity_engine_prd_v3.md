# Micro-SaaS Opportunity Engine – Product Requirements Document (v3.0)

**Version:** 3.0 (Post-Review Update)  
**Status:** In Development  
**Goal:** Deliver a dynamic, evidence-backed idea generator that produces exportable, theme-relevant opportunities with clear validation signals.

---

## 1. Context
Solo founders waste time building unvalidated ideas. The current PoC leans on static data, brittle keyword checks, and ignores user themes during ingestion. v3 focuses on making every output traceable to fresh external signals (search, web content), enforcing theme relevance, and producing exportable artifacts for further analysis.

## 2. User Stories
- As a founder, I want to input a theme (e.g., "vertical SaaS for dentists") and receive ideas that clearly match that theme with evidence of demand.
- As a founder, I want to rate and export results to CSV/Markdown without re-running commands.
- As a founder, I want recommendations to be gated by real-world signals (search volume, trend) so I can trust “Green/Build” calls.

## 3. Functional Requirements

### 3.1 Data Ingestion (Researcher)
- **Dynamic Web Ingestion:** Query external search sources (e.g., Google/Bing APIs, Reddit, Hacker News) using theme-aware prompts. Avoid static curated datasets.
- **Theme Enforcement:** All retrieved documents must be semantically filtered to the provided `theme`; irrelevant items are rejected.
- **Deduping & Coverage:** Each refinement loop must issue varied queries (e.g., `"<theme> pain points"`, `"<theme> alternatives"`, `"<theme> buyer complaints"`). Deduplicate ideas by title/semantic similarity.
- **Freshness:** Prefer content from the last 6–12 months; flag older sources.

### 3.2 External Evidence Provider
- **SEO Metrics:** Fetch search volume, keyword difficulty (0–100), and 12‑month trend direction for each idea keyword/title via an SEO API (e.g., DataForSEO, SEMRush).
- **Resilience:** Handle missing metrics gracefully (retry/backoff, mark as `unknown`).
- **Audit Trail:** Store the raw metric source and timestamp for traceability.

### 3.3 Scoring & Recommendation
- **Semantic Scoring:** Use embeddings-based similarity for Pain/Solution/ICP relevance instead of keyword heuristics; quantify relevance (0–1 or 0–100) with rationales that cite semantic signals.
- **Pricing Parsing:** Recognize formats such as currency symbols, ranges ("$20–30/mo"), "Freemium", and "Contact Sales" without defaulting to `Unknown`.
- **Validation Gate:** A "Green/Build" recommendation requires at least one positive external signal (e.g., Rising trend or search volume > 1,000) in addition to internal scores.
- **Explainability:** Every score must include a short rationale referencing evidence (e.g., "Rising search interest + clear ICP pain").

### 3.4 CLI Workflow & Exports
- **Unified Flow:** Single command performs `run -> display -> prompt for rating -> export`. Eliminate split `run`/`rate` steps.
- **Inline Rating:** After showing results, prompt the user to rate ideas without restarting the process; persist feedback.
- **Export Options:** Provide CSV and Markdown exports of the ranked table, including all evidence fields and user ratings. Confirm export path to the user.
- **Non-Interactive Defaults:** Allow a flag to auto-export without prompts for batch use.

### 3.5 Data Model
Extend `Idea` to include external evidence and pricing clarity:
```python
@dataclass
class Idea:
    title: str
    icp: str
    pain: str
    solution: str
    revenue_model: str
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[int] = None  # 0-100
    trend_status: str = "Unknown"  # Rising, Stable, Falling, Unknown
    pricing_notes: Optional[str] = None  # normalized from parsed pricing
    scores: IdeaScores
    recommendation: str
    key_risks: List[str]
    source_urls: List[str] = field(default_factory=list)  # audit trail
```

## 4. Non-Functional Requirements
- **Performance:** Full run completes within 90 seconds for a single theme with default limits (e.g., top 20 ideas).
- **Reliability:** Network/API failures degrade gracefully with clear user messaging; partial results are allowed but flagged.
- **Compliance:** Avoid storing personal data; limit requests to public sources and documented APIs.

## 5. Acceptance Criteria
- Theme keyword appears in >90% of idea titles or rationales; irrelevant items are excluded.
- "Green/Build" ideas always show at least one populated external metric supporting the recommendation.
- Exports include columns for search volume, keyword difficulty, trend status, and pricing notes.
- CLI run ends by prompting for rating and export; CSV/Markdown files are written to the specified directory and paths are displayed.
- Scoring rationales reference semantic signals rather than exact keyword matches.

## 6. Roadmap

### 🚀 NOW (0–4 weeks) — Real Data
1) Implement search/ingestion that is theme-aware with varied queries and deduping.  
2) Integrate SEO metrics provider to populate search volume, keyword difficulty, and trend status.  
3) Build unified CLI flow with inline rating and CSV/Markdown export helpers.  
4) Normalize pricing parsing and surface pricing notes in outputs/exports.

### 🔮 NEXT (4–8 weeks) — Intelligence
1) Replace heuristic scoring with embeddings-based semantic scoring and rationales.  
2) Add SQLite persistence for historical runs and user feedback.  
3) Introduce validation gate logic that combines semantic scores with external metrics before recommending "Green/Build".

### 🔭 LATER (8+ weeks) — Agentic
1) Reintroduce multi-agent debate only after data quality is validated.  
2) Generate lightweight landing pages for top ideas as smoke tests.  
3) Optional: add workflow automation to continuously monitor trends for saved themes.

## 7. Metrics
- **Data Freshness:** % of sources <= 6 months old.  
- **Theme Relevance:** Average user rating on relevance (0–5).  
- **Validation Coverage:** % of ideas with at least one external metric populated.  
- **Recommendation Accuracy:** % of "Green/Build" ideas meeting the validation gate.  
- **Export Usage:** # of successful export actions per run.

## 8. Risks & Mitigations
- **API Limits/Cost:** Use cached results and configurable quotas; surface errors cleanly.  
- **Semantic Drift:** Periodically evaluate embedding model relevance against user feedback; allow model configuration.  
- **Data Staleness:** Include timestamps and source URLs; prioritize recent content during ingestion.

