# Micro-SaaS Opportunity Engine

A tool to surface high-confidence, low-complexity micro-SaaS ideas.

## Project Structure

- `src/`: Source code for the engine.
- `data/`: Datasets and input files (JSON, TXT).
- `docs/`: Documentation including PRD and worklogs.
- `tests/`: Unit tests (to be added).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the engine with a theme (defaults to loading feedback from `data/user_feedback.json` when present):

```bash
python -m src.saas_opportunity_engine run "micro saas for accountants"
```

### Options

- `--dataset`: Path to a JSON file containing ideas.
- `--feedback`: Path to a JSON file containing user feedback (defaults to `data/user_feedback.json`).

Example with custom dataset:

```bash
python -m src.saas_opportunity_engine run "legal tech" --dataset=data/micro_saas_ideas_expanded_v5.json
```

### Capturing user ratings

Use the `rate` subcommand to list the top ideas, capture 0–5 ratings, and persist them to `data/user_feedback.json` (or a custom `--feedback` path):

```bash
python -m src.saas_opportunity_engine rate "micro saas for accountants" --top 5
```

Each rating is stored against the idea title and automatically reused on subsequent `run` commands to adjust totals. Ratings map linearly to score adjustments: 0 → -5, 2.5 → 0, 5 → +5, keeping recommendations aligned with the ScoringEngine thresholds.
