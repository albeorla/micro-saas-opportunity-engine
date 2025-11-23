# Micro‑SaaS Opportunity Engine – Updated Product Requirements Document

This document captures the updated requirements for the **Micro‑SaaS Opportunity Engine**, reflecting the current state of the project and outlining the next steps for development.  It is organised around the Now/Next/Later roadmap and incorporates the implementation progress to date.

## 1. Context and Goal

Solo founders and indie hackers often burn time and money chasing unvalidated ideas.  The goal of this project is to build a tool that repeatedly surfaces **high‑confidence, low‑complexity micro‑SaaS ideas** with clear demand, realistic revenue potential, and actionable next steps.  The system should be able to take a broad theme (e.g. “B2B SaaS for accountants”) and output a ranked list of opportunities with supporting evidence and recommendations.

## 2. What’s been built so far

### MVP implementation

- An initial **Python script (`saas_opportunity_engine.py`)** has been created in the container environment.  The script demonstrates the full flow from idea input to scoring and recommendation.
- It uses a **static dataset** of five micro‑SaaS ideas drawn from a 2025 article on profitable micro‑SaaS opportunities【566476804201456†L100-L124】.  Each idea includes the ideal customer profile (ICP), pain point, solution concept, revenue model and key risks.
- A **heuristic scoring engine** assigns numeric scores for demand (0–30), acquisition (0–20), MVP complexity (0–20), competition (0–20) and revenue velocity (0–10).  The scores are derived from simple rules: for example, high pain and cost indicate strong demand; narrow pricing suggests less competition; low pricing speeds adoption, etc.
- The total score determines a **recommendation**:
  - **green_build** (build the MVP now) if total ≥ 75 and demand and acquisition scores are high.
  - **yellow_validate** (validate specific assumptions first) if total ≥ 65.
  - **red_kill** otherwise.
- The script prints a **table** of the ideas sorted by total score, along with the scores and recommendations.  It serves as an end‑to‑end proof of concept.

### Improvements added in this update

Several significant enhancements have been incorporated:

1. **Dataset extensibility via JSON** – the engine now accepts a `--dataset` argument pointing to a JSON file of ideas.  When provided, the engine loads the ideas from this file; otherwise it uses the built‑in sample dataset.  This makes it easy to extend or customise the idea pool without modifying code.
2. **Sample dataset format** – the script documents an example JSON format (see the appendix) so that users can craft their own idea lists.  Each entry includes the fields `title`, `icp`, `pain`, `solution`, `revenue_model`, and `key_risks`.
3. **Researcher component** – a new `Researcher` class simulates automated research by returning additional micro‑SaaS ideas drawn from authoritative sources. It now supports **configurable sources** and **deduplication**, and can parse ideas from both local files and remote URLs (with basic scraping).
4. **Critique & refinement loop** – the engine includes a feedback loop. After scoring, it checks for high-quality ideas. If none are found, it fetches new ideas from the Researcher and repeats the process.
5. **Refactored run logic** – the `run()` method orchestrates the iteration, scoring and refinement steps.
6. **Source credibility and feedback adjustments** – A **Critic** component adjusts scores based on source credibility and recency. A **UserFeedbackManager** allows users to rate ideas (0–5), which adjusts the final score.
7. **CLI Improvements** – The CLI now supports subcommands: `run` (standard execution) and `rate` (interactive rating mode).
8. **Configurable Scoring** – A `data/scoring_config.json` file allows users to tune scoring thresholds and price-band adjustments without changing code.
9. **Unit Tests** – A `tests/` directory with `pytest` coverage ensures core logic stability.

## 3. Updated Now/Next/Later roadmap

### NOW (0–4 weeks)

The focus is on usability, reliability, and refining the "intelligence" of the system.

1.  **Enhanced Critique (Priority 1)**: Improve the `Critic` to be smarter about "credibility". Currently, it uses simple heuristics. We should add:
    *   Domain authority checking (allowlist/blocklist).
    *   Better date parsing to penalize stale ideas.
    *   "Novelty" detection (down-weighting generic ideas).
2.  **Web Interface (Priority 2)**: Build a simple web UI (e.g., Streamlit or Flask) to replace/augment the CLI. This will make "rating" and "exploring" ideas much easier.
3.  **Refinement Loop Improvements**: Make the "reflexion" loop smarter. Instead of just "more ideas", it should look for *specific* missing types of ideas (e.g., "We have too many B2B ideas, look for B2C").

### NEXT (4–12 weeks)

1.  **Automated Web Ingestion**: Fully automate the "Researcher" to search the web for *new* articles dynamically (using a search API or browser tool) rather than just scraping a fixed list of URLs.
2.  **Persistent Database**: Move from JSON files to a proper database (SQLite) to handle thousands of ideas and history.
3.  **Multi-Agent Debate**: Implement a "Committee" of agents (CEO, CTO, Product) to debate the top ideas before showing them to the user.

### LATER (12+ weeks)

1.  **Meta-evaluation and RL**: Use historical feedback to train the scoring weights automatically.
2.  **Marketplace Integration**: Connect to platforms where these ideas could be validated (e.g., landing page generators).
3.  **Self-service Builder**: Generate a project skeleton for the chosen idea.

## 4. Open questions and risks

1. **Data sources**: identifying reliable, up‑to‑date sources of micro‑SaaS ideas is challenging.  Scraping must avoid SEO spam and prioritise authoritative sources such as Gartner or industry blogs.
2. **Scoring calibration**: the heuristic scores need calibration against real business outcomes; otherwise they could bias towards certain types of ideas (e.g. AI heavy) without real market demand.
3. **Legal and privacy considerations**: collecting and processing data about potential customers must comply with data protection laws.  High‑impact decisions based on sensitive attributes are explicitly out of scope.
4. **Maintaining user trust**: recommendations must be transparent, with clear rationales and citations for each idea.  Black‑box scoring could erode confidence.

## 5. Appendix – Example JSON format

Users who wish to extend the dataset can create a JSON file with an array of idea objects.  Each object should have the following keys:

```json
[
  {
    "title": "AI‑powered scheduling assistant for lawyers",
    "icp": "Small law firms",
    "pain": "Scheduling client meetings and court appearances is manual and prone to conflicts",
    "solution": "Automated scheduler that integrates with case management and court calendars",
    "revenue_model": "$29–99/month per lawyer",
    "key_risks": [
      "Requires integration with sensitive legal calendars",
      "Law firms may resist adopting new technology"
    ]
  },
  {
    "title": "… another idea …",
    "icp": "…",
    "pain": "…",
    "solution": "…",
    "revenue_model": "…",
    "key_risks": ["…", "…"]
  }
]
```

Save this JSON file and run the script with the `--dataset` argument:

```bash
python -m src.saas_opportunity_engine "legal tech" --dataset=/path/to/ideas.json
```

## 6. Conclusion

The Micro‑SaaS Opportunity Engine is now past the proof‑of‑concept stage: a working script outputs ranked, scored opportunities based on a curated dataset and simple heuristics.  The next iterations should focus on real data ingestion, richer evaluation and interactive capabilities.  This PRD will evolve as the system grows.