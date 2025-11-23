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

Run the engine with a theme:

```bash
python -m src.saas_opportunity_engine "micro saas for accountants"
```

### Options

- `--dataset`: Path to a JSON file containing ideas.
- `--feedback`: Path to a JSON file containing user feedback.

Example with custom dataset:

```bash
python -m src.saas_opportunity_engine "legal tech" --dataset=data/micro_saas_ideas_expanded_v5.json
```
