# Micro-SaaS Opportunity Engine

A tool to surface high-confidence, low-complexity micro-SaaS ideas.

#The goal is to help solo founders and indie hackers avoid building things nobody wants by providing a scored, evidence-backed list of opportunities.

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the current development plan and future goals.

## Project Structure

- `src/`: Source code for the engine.
- `data/`: Datasets and input files (JSON, TXT).
- `docs/`: Documentation including PRD and worklogs.
- `tests/`: Unit tests (to be added).

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The first run will download a ~400MB sentence-transformers model for semantic scoring. This is a one-time download that may take 1-2 minutes depending on your connection.

### 2. Configure API Keys (Required for Real Data)

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

#### **Required: Bing Search API**
Without this key, the system falls back to 5 curated ideas instead of dynamic web research.

1. Get a free Azure account: https://azure.microsoft.com/free/
2. Create a Bing Search v7 resource: https://portal.azure.com
3. Copy your API key to `.env`:
   ```bash
   BING_SEARCH_API_KEY=your_key_here
   ```

#### **Optional: SEO Metrics API**
Without this, the system uses simulated metrics (fine for testing logic, not for real decisions).

The code expects a JSON API that returns:
```json
{
  "search_volume": 1500,
  "keyword_difficulty": 45,
  "trend_direction": "upward"
}
```

**Options:**
- Build a proxy around DataForSEO, SEMRush, or Ahrefs
- Use simulated metrics for development (default behavior)

See `.env.example` for configuration details.

## Usage

### Quick Start

Run the engine with a theme:

```bash
python -m src.saas_opportunity_engine run "vertical saas for dentists" --export-csv results.csv --rate-top 3
```

This will:
1. Search for ideas related to your theme (web search if Bing API is configured, or curated fallbacks)
2. Score each idea using AI embeddings for pain/complexity analysis
3. Display a ranked table with recommendations (Green/Yellow/Red)
4. Prompt you to rate the top 3 ideas (0-5 scale)
5. Export results to `results.csv`

### Command Options

**Run Command** (default):
```bash
python -m src.saas_opportunity_engine run "<theme>" [OPTIONS]
```

Options:
- `--export-csv PATH`: Export results to CSV file
- `--export-md PATH`: Export results to Markdown table
- `--rate-top N`: Prompt to rate top N ideas (default: 5, use 0 to skip)
- `--dataset PATH`: Use custom JSON dataset instead of dynamic search
- `--feedback PATH`: Path to feedback file (default: `data/user_feedback.json`)
- `--urls URL1,URL2`: Comma-separated URLs to scrape for ideas
- `--config PATH`: JSON/YAML config for researcher settings
- `--min-credibility low|medium|high`: Filter ideas by credibility

**Rate Command** (standalone rating session):
```bash
python -m src.saas_opportunity_engine rate "<theme>" --top 5
```

### Understanding the Output

**Recommendation Levels:**
- **Green (Build)**: High scores + external validation (search volume > 1000 OR rising trend)
- **Yellow (Validate)**: Good scores but needs market validation
- **Red (Kill)**: Low scores or major blockers

**Score Dimensions:**
- **Demand**: Pain severity (semantic analysis of problem description)
- **Acquisition**: How easy to reach the target audience
- **MVP Complexity**: Build difficulty (semantic analysis of solution)
- **Competition**: Market crowdedness
- **Revenue Velocity**: Speed of customer acquisition based on pricing

### Working with Feedback

Ratings map to score adjustments:
- 0 stars → -5 points
- 2.5 stars → 0 points (neutral)
- 5 stars → +5 points

Feedback persists across runs and influences future rankings.

### Examples

**Basic theme search:**
```bash
python -m src.saas_opportunity_engine run "legal tech"
```

**Custom dataset with export:**
```bash
python -m src.saas_opportunity_engine run "accounting" --dataset data/custom_ideas.json --export-csv output.csv
```

**Web scraping with credibility filter:**
```bash
python -m src.saas_opportunity_engine run "healthcare" --urls https://example.com/ideas --min-credibility high
```
