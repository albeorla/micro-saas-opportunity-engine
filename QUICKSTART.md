# Quickstart Guide

Get the Micro-SaaS Opportunity Engine running in 5 minutes.

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First run downloads a ~400MB AI model (one-time, takes 1-2 minutes).

---

## 2. Configure API (Optional but Recommended)

### Without API Key (Test Mode)
The system works immediately with 5 curated ideas. Good for testing, not for real research.

### With API Key (Production Mode)
Get real-time web search results:

```bash
# 1. Create .env file
cp .env.example .env

# 2. Get free Bing Search API key
# Visit: https://portal.azure.com
# Create: Bing Search v7 resource
# Copy your key to .env:
#   BING_SEARCH_API_KEY=your_key_here
```

---

## 3. Run Your First Search

```bash
python -m src.saas_opportunity_engine run "vertical saas for dentists" --export-csv results.csv --rate-top 3
```

This will:
1. Search for ideas (web search if configured, else curated fallback)
2. Score using AI embeddings
3. Display ranked table with Green/Yellow/Red recommendations
4. Prompt to rate top 3 ideas (0-5 stars)
5. Export to `results.csv`

---

## 4. Understand the Output

### Recommendation Colors

- **🟢 Green (Build):** High scores + market validation (search volume > 1000 OR rising trend)
- **🟡 Yellow (Validate):** Good internal scores but needs external proof
- **🔴 Red (Kill):** Low scores or major blockers

### Score Dimensions (0-100 total)

- **Demand (30):** Pain severity (semantic analysis)
- **Acquisition (20):** Ease of reaching target customers
- **MVP Complexity (20):** Build difficulty
- **Competition (20):** Market crowdedness
- **Revenue Velocity (10):** Speed of customer acquisition

### Rating System

Your 0-5 star ratings adjust scores:
- 0 stars → -5 points
- 2.5 stars → no change
- 5 stars → +5 points

Ratings persist in `data/user_feedback.json` and apply to future runs.

---

## 5. Common Commands

### Basic search
```bash
python -m src.saas_opportunity_engine run "legal tech"
```

### Search with export
```bash
python -m src.saas_opportunity_engine run "healthcare saas" --export-csv healthcare.csv
```

### Custom dataset
```bash
python -m src.saas_opportunity_engine run "accounting" --dataset data/my_ideas.json
```

### Standalone rating session
```bash
python -m src.saas_opportunity_engine rate "my theme" --top 5
```

---

## 6. Troubleshooting

### Model download appears frozen
First run downloads ~400MB. Wait 1-2 minutes. You'll see:
```
[ScoringEngine] Loading semantic scoring model (one-time download, ~400MB)...
```

### Only getting 5 ideas
You're in fallback mode (no Bing API key). Either:
- Configure `BING_SEARCH_API_KEY` in `.env` for live search
- Use `--dataset` flag to load custom ideas from JSON

### SEO metrics look fake
Without `SEO_API_BASE_URL`, the system uses deterministic simulated data. This is fine for testing logic but not for real decisions. See `.env.example` for setup.

### Export prompt skipped in scripts
The export prompt only appears in interactive terminals. Use `--export-csv` flag in scripts/automation.

---

## 7. Next Steps

- Read `docs/MVP_STATUS.md` for architecture details
- Review `docs/micro_saas_opportunity_engine_prd_v3.md` for full requirements
- Check `.env.example` for advanced configuration
- Run `pytest tests/` to verify your setup

---

**Questions?** File an issue or review the comprehensive docs in `/docs`.
