Here is the rewritten **Product Requirements Document (PRD)**.

This version incorporates the critical feedback from the review, specifically addressing the circular "confidence" definition, the broken theme filtering, the lack of real-time data, and the brittle scoring logic.

-----

# Micro‑SaaS Opportunity Engine – Product Requirements Document (v2.0)

**Version:** 2.0 (Post-Audit Update)
**Status:** In Development
**Goal:** Transition from Static PoC to Dynamic Intelligence Engine

## 1\. Context and Problem Statement

Solo founders and indie hackers often burn resources building unvalidated ideas. While the current Proof-of-Concept (PoC) scores ideas based on internal text heuristics, it lacks **external market validation**.

The goal of the **Micro‑SaaS Opportunity Engine** is to surface opportunities that are not just "good on paper" but **validated by external demand signals**. The system must take a user-defined theme (e.g., "B2B SaaS for accountants") and output a ranked list of opportunities backed by **live search volume**, **keyword difficulty**, and **freshness**, rather than relying solely on static curated lists.

## 2\. Core Functional Requirements

### 2.1 The "Researcher" (Data Ingestion)

**Current Gap:** The existing implementation relies on a static JSON dataset and ignores the user's `theme` input.
**New Requirement:**

  * **Dynamic Web Ingestion:** The Researcher must actively query external sources (e.g., Google Custom Search API, Reddit API) using the user's `theme` to fetch fresh content.
  * **Theme Filtering:** The system must strictly filter or prioritize ideas that semantically match the provided `theme`.
  * **Deduping Strategy:** Refinement loops must query *new* keywords (e.g., `theme + "pain points"`, `theme + "alternatives"`) rather than recycling the same static list.

### 2.2 The "Scoring Engine" (Intelligence)

**Current Gap:** Scoring relies on brittle keyword matching (e.g., checking for specific strings like "manual" or "expensive").
**New Requirement:**

  * **Semantic Scoring:** Replace exact string matching with **semantic analysis** (e.g., embedding similarity) to identify pain points regardless of specific phrasing (e.g., recognizing that "exhausting" implies "high demand").
  * **Robust Parsing:** Pricing extraction must handle unstructured formats (e.g., "Contact Sales", "Freemium", "£50/mo") without defaulting to "Unknown".

### 2.3 The "Evidence" Model (Validation)

**Current Gap:** "Confidence" is currently an internal consistency score.
**New Requirement:**

  * **External Metrics:** The `Idea` model must be expanded to include:
      * **Search Volume:** Monthly search volume for the primary keyword.
      * **Keyword Difficulty:** Competition metric (0–100).
      * **Trend Direction:** (Rising/Falling/Stable) based on a 12-month trailing window.
  * **Validation Gate:** A "Green/Build" recommendation **requires** at least one positive external signal (e.g., Rising Trend or High Search Volume).

## 3\. Revised Roadmap

The roadmap has been reordered to prioritize data integrity and validation over advanced agentic features.

### 🚀 NOW (0–4 weeks) — *The "Real Data" Phase*

**Focus:** Connecting the engine to the real world.

1.  **Dynamic Web Ingestion (Priority Critical):** Implement a search API (e.g., Google/Bing) to fetch live articles based on the input `theme`.
2.  **Fix Theme Logic:** Ensure the `Researcher` actually uses the `theme` argument to filter results.
3.  **Export Artifacts:** Add a feature to export the ranked table to **CSV** or **Markdown** so users can analyze results in external tools (Excel/Notion).
4.  **Unified CLI:** Streamline the workflow. Instead of separate `run` and `rate` commands, the flow should be `run` -\> `display` -\> `prompt: "Rate these ideas?"` -\> `export`.

### 🔮 NEXT (4–8 weeks) — *The "Intelligence" Phase*

**Focus:** Improving the quality of analysis.

1.  **Semantic Scoring:** Implement a lightweight embeddings model (e.g., `sentence-transformers`) to score "Pain" and "Solution" quality more accurately than keyword lists.
2.  **External API Integration:** Connect to an SEO/Keywords API (e.g., DataForSEO, SEMRush) to populate the new "Evidence" fields.
3.  **Persistent Database:** Migrate from JSON files to **SQLite** to store historical searches and feedback.

### 🔭 LATER (8+ weeks) — *The "Agentic" Phase*

**Focus:** Automation and synthesis.

1.  **Multi-Agent Debate:** Re-introduce the "Committee of Agents" (CEO, CTO, Product) only *after* the data layer is robust.
2.  **Landing Page Generation:** Auto-generate a "Smoke Test" landing page for the top-rated idea.

## 4\. User Journey (Target State)

1.  **Input:** User runs `python -m src.engine "vertical SaaS for dentists"`.
2.  **Search:** The system queries the web for "dentist software pain points 2025" and "dentist practice management trends."
3.  **Processing:**
      * It extracts 20 raw ideas.
      * It filters them for relevance to "dentists."
      * It checks keyword volume for the top 5 (e.g., "dental scheduling software").
4.  **Output:** A table displays the top ideas, including a new column: **"Search Trend: 📈 (+15%)"**.
5.  **Interaction:** The system asks: *"Do you want to rate these ideas or export to CSV?"*
6.  **Action:** User selects "Export," and a `.csv` file is generated.

## 5\. Success Metrics

  * **Data Freshness:** % of ideas sourced from content published in the last 6 months.
  * **Relevance:** User rating (0–5) of how well the output matches the input `theme`.
  * **Validation Rate:** % of "Green" recommendations that have a verified Search Volume \> 1,000/month.

## 6\. Appendix: Data Structure Updates

The `Idea` object will be updated to support the new requirements:

```python
@dataclass
class Idea:
    title: str
    icp: str
    pain: str
    solution: str
    revenue_model: str
    # NEW FIELDS
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[int] = None
    trend_status: str = "Unknown"  # Rising, Stable, Falling
    # Existing fields
    scores: IdeaScores
    recommendation: str
    key_risks: List[str]
```