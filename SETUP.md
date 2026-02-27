# Sector News Tracker — Setup & Deployment Guide

## Project Structure

```
sector-news-tracker/
├── .github/
│   └── workflows/
│       └── fetch_news.yml      # GitHub Actions cron job (hourly)
├── .streamlit/
│   └── config.toml             # Streamlit theme config
├── data/
│   ├── _meta.json              # Last fetch metadata
│   ├── technology.json          # Auto-generated per sector
│   ├── banking_finance.json
│   └── ...
├── app.py                       # Streamlit frontend dashboard
├── config.py                    # Sector definitions & settings
├── fetch_news.py                # News fetching backend script
├── requirements.txt
├── .gitignore
└── SETUP.md                     # This file
```

---

## Step 1: Get a Free GNews API Key

1. Go to **https://gnews.io/** and sign up (free).
2. The free plan gives you **100 requests/day** — more than enough for hourly
   fetches across all sectors.
3. Copy your API key from the dashboard.

---

## Step 2: Create a GitHub Repository

1. Go to **https://github.com/new** and create a new repository
   (e.g., `sector-news-tracker`). Make it **public** (required for free
   Streamlit Cloud hosting).
2. Push this project to the repo:

```bash
cd sector-news-tracker
git init
git add .
git commit -m "Initial commit: sector news tracker"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sector-news-tracker.git
git push -u origin main
```

---

## Step 3: Add Your API Key as a GitHub Secret

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**.
2. Click **"New repository secret"**.
3. Name: `GNEWS_API_KEY`
4. Value: paste your GNews API key.
5. Click **"Add secret"**.

This keeps your API key secure — the GitHub Actions workflow reads it from
the secret, never from the code.

---

## Step 4: Enable GitHub Actions

1. Go to the **Actions** tab in your repo.
2. You should see the "Fetch Sector News" workflow listed.
3. Click **"Enable"** if prompted.
4. To test immediately, click the workflow → **"Run workflow"** → **"Run"**.
5. After it runs (~2 minutes), check the `data/` folder — it should now
   contain JSON files with articles.

The cron schedule `0 * * * *` runs the workflow at the top of every hour,
24/7, regardless of whether your laptop is on.

---

## Step 5: Deploy the Dashboard on Streamlit Community Cloud (Free)

1. Go to **https://share.streamlit.io/** and sign in with your GitHub account.
2. Click **"New app"**.
3. Fill in:
   - **Repository**: `YOUR_USERNAME/sector-news-tracker`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **"Deploy!"**

Your dashboard will be live at:
`https://YOUR_USERNAME-sector-news-tracker.streamlit.app`

Every time the GitHub Actions workflow pushes new data, Streamlit Cloud
automatically picks up the changes (with a ~5 minute cache TTL).

---

## Step 6: (Optional) Run Locally

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export GNEWS_API_KEY="your_key_here"   # On Windows: set GNEWS_API_KEY=your_key_here

# Fetch news manually
python fetch_news.py

# Run the dashboard
streamlit run app.py
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                      │
│  (cron: every hour)                                  │
│                                                      │
│  1. Runs fetch_news.py                               │
│  2. Queries GNews API + RSS feeds                    │
│  3. Merges & deduplicates articles                   │
│  4. Writes JSON files to data/                       │
│  5. Commits & pushes to repo                         │
└────────────────────┬────────────────────────────────┘
                     │ git push
                     ▼
┌─────────────────────────────────────────────────────┐
│              GitHub Repository                       │
│                                                      │
│  data/technology.json                                │
│  data/banking_finance.json                           │
│  data/healthcare.json                                │
│  ...                                                 │
└────────────────────┬────────────────────────────────┘
                     │ auto-deploy
                     ▼
┌─────────────────────────────────────────────────────┐
│          Streamlit Community Cloud                   │
│                                                      │
│  Reads JSON from repo → renders dashboard            │
│  Accessible from anywhere via browser                │
└─────────────────────────────────────────────────────┘
```

---

## Customization

### Add a New Sector

Edit `config.py` and add an entry to the `SECTORS` dict:

```python
"Automotive": {
    "queries": [
        "automotive industry news",
        "electric vehicle market",
        "car manufacturing business",
    ],
    "rss_feeds": [],
},
```

The new sector will automatically appear in the dashboard dropdown after the
next fetch run.

### Change Fetch Frequency

Edit `.github/workflows/fetch_news.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: "0 */2 * * *"   # Every 2 hours
  - cron: "*/30 * * * *"  # Every 30 minutes (watch API limits)
```

### Increase Article Limit

In `config.py`, change `MAX_ARTICLES_PER_SECTOR` (default: 50).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No articles appearing | Check that `GNEWS_API_KEY` secret is set correctly in GitHub |
| GitHub Actions not running | Go to Actions tab → enable workflows |
| "API quota exhausted" in logs | Free tier = 100 req/day. Reduce sectors or frequency |
| Streamlit app shows old data | TTL cache is 5 min. Wait or refresh. |
| RSS feeds failing | Some feeds block automated requests. This is expected — GNews is the primary source. |
