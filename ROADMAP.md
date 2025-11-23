# Micro-SaaS Opportunity Engine Roadmap

This document outlines the development roadmap for the Micro-SaaS Opportunity Engine. It follows a Now/Next/Later format to prioritize immediate value while keeping long-term goals in view.

## 🚀 NOW (0–4 weeks)
**Focus:** Usability, Reliability, and "Intelligence" Refinement.

- [x] **Polish Command-Line Tool**: Refactor into a modular entry point with subcommands (`run`, `rate`).
- [x] **Configurable Scoring**: Allow users to tune thresholds via `data/scoring_config.json`.
- [x] **Unit Tests**: Establish a `tests/` directory with `pytest` coverage.
- [ ] **Enhanced Critique (Priority 1)**: Improve `Critic` with domain authority checks, better date parsing, and novelty detection.
- [ ] **Web Interface (Priority 2)**: Build a simple web UI (Streamlit/Flask) for easier idea exploration and rating.
- [ ] **Refinement Loop Improvements**: Enhance the "reflexion" loop to search for specific missing niches.

## 🔮 NEXT (4–12 weeks)
**Focus:** Dynamic Research and Data Persistence.

- [ ] **Automated Web Ingestion**: Fully automate the `Researcher` to dynamically search the web for new articles using a search API or browser tool.
- [ ] **Persistent Database**: Migrate from JSON files to SQLite to handle thousands of ideas and historical data.
- [ ] **Multi-Agent Debate**: Implement a "Committee" of agents (CEO, CTO, Product) to debate top ideas before presentation.

## 🔭 LATER (12+ weeks)
**Focus:** Learning, Optimization, and Ecosystem.

- [ ] **Meta-evaluation and RL**: Use historical feedback to automatically train scoring weights.
- [ ] **Marketplace Integration**: Connect to platforms for idea validation (e.g., landing page generators).
- [ ] **Self-service Builder**: Generate project skeletons for chosen ideas.
