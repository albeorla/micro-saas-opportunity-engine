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
3. **Researcher component** – a new `Researcher` class simulates automated research by returning additional micro‑SaaS ideas drawn from an authoritative 2025 article.  In a full version this module would crawl official sources; in the MVP it provides a handful of extra ideas that the engine can incorporate when needed.
4. **Critique & refinement loop** – the engine now includes a simple feedback loop.  After each scoring iteration it checks whether at least one idea has a `green_build` recommendation.  If not, the engine removes ideas with `red_kill` recommendations, fetches new ideas from the Researcher, and repeats the scoring.  This process iterates up to three times, mimicking a basic self‑improvement cycle where the system critiques its output and broadens its search if necessary.
5. **Refactored run logic** – the `run()` method orchestrates the iteration, scoring and refinement steps, then prints the final ranked table.  This paves the way for adding more sophisticated critique or multi‑agent patterns in the next phase.

6. **Source credibility, recency and feedback adjustments** – a new **Critic** component has been implemented in the Python engine.  Ideas may now optionally include `credibility` (`high`, `medium` or `low`) and `source_date` (YYYY-MM-DD) fields.  The critic awards a small bonus for high‑credibility sources and penalises low credibility or outdated ideas (older than three years).  A **UserFeedbackManager** reads a JSON file of user ratings (0–5) and translates those into score adjustments.  Both mechanisms adjust each idea’s final total score and influence the recommendation decision, enabling the engine to down‑weight SEO‑driven or stale ideas and incorporate real user feedback.

7. **Feedback CLI option** – the command-line interface now accepts a `--feedback` argument.  When supplied with a path to a JSON file mapping idea titles to user ratings, the engine will use these ratings to boost or penalise ideas, making it easier to calibrate scoring heuristics over time.

8. **Project Restructuring and Modularization** – The codebase has been reorganized into a standard Python project structure (`src/`, `data/`, `docs/`) and the monolithic script has been split into focused modules (`models`, `scoring`, `researcher`, `critic`, `feedback`, `engine`) to improve maintainability and scalability.

## 3. Updated Now/Next/Later roadmap

### NOW (0–4 weeks)

The focus is on getting a working prototype that demonstrates the core loop: idea ingestion → scoring → recommendation.

1. **Polish the command‑line tool**: *Completed.* The CLI has been refactored into a modular entry point (`src.saas_opportunity_engine`) with improved argument handling.
2. **Improve scoring heuristics**: refine the heuristic rules based on real user feedback and data.  For example, incorporate more precise weighting for price bands or complexity factors.
3. **Expand the seed dataset**: *Completed.* The dataset has expanded to **75 ideas**.
4. **Add unit tests**: *In Progress.* A `tests/` directory has been created. Modularization facilitates easier unit testing of individual components.
5. **Document usage**: *Completed.* A `README.md` has been created explaining installation and usage.

### NEXT (4–12 weeks)

The next phase will make the engine more dynamic and incorporate feedback loops.

**Priority 1 – Automated research module**: Build a Python‑based researcher capable of extracting bullet‑point ideas from trusted articles and reports.  The researcher should parse pains, solutions and pricing from structured lists (e.g. blog posts, trend round‑ups).  Initially this may rely on predetermined sources stored locally; later it can call the browser tool to fetch new pages and use a scraper to extract data.  The output must be converted into the same idea format and include optional metadata fields (`source`, `source_date`, `credibility`).  This task is critical because it moves the system beyond a fixed dataset and ensures a steady pipeline of new, high‑quality ideas.

**Priority 2 – Feedback-driven scoring calibration**: Develop a mechanism for users to rate the relevance and quality of each idea (0–5) through a simple interface (command‑line or web).  Store these ratings in a JSON file that the engine reads via the `--feedback` argument.  Adjust scoring thresholds and total scores based on user feedback, allowing the engine to learn which heuristics correlate with real success.  Over time this will enable data‑driven calibration of the scoring model.

3. **Enhanced critique and filtering**: Extend the critic to incorporate source credibility (e.g. official reports vs. SEO spam), recency of publication, and novelty of the idea.  Ideas with weak or outdated evidence should have their total scores reduced.  Use publication dates and domain reputation to infer credibility.  This builds on the initial critic that already handles credibility and recency adjustments.

4. **Refinement loop**: Allow the engine to iterate on its own output by analysing gaps in coverage and generating new sub‑queries (e.g. niches not yet explored).

5. **Persistent memory**: Store previous runs and feedback so the engine avoids repeating poor ideas and learns which heuristics correlate with real success.

6. **Interactive UI / dashboard**: Build a simple web or command‑line interface where users can view and filter opportunities, tweak scoring weights and provide feedback on recommendations.

### LATER (12+ weeks)

Longer‑term improvements will focus on learning and optimisation.

1. **Meta‑evaluation and RL**: use historical success/failure data to adjust scoring weights and refine heuristics via reinforcement learning or Bayesian optimisation.
2. **Competition tracking**: monitor competitor products and pricing to dynamically adjust competition scores.
3. **Self‑service micro‑SaaS builder**: integrate templates or scaffolding generators to spin up basic SaaS services based on the top ideas.
4. **Marketplace integration**: allow users to publish, share or sell validated ideas or pre‑built micro‑SaaS solutions.
5. **Multi‑agent debate**: experiment with multi‑agent approaches (e.g. debate, committee) to ensure diverse perspectives on the viability of each idea.

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