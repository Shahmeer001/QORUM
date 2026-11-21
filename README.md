# QUORUM

**Cross-Market Multi-Agent Decisions with Supervised Debate**

QUORUM is an intelligent trading decision architecture where specialized autonomous agents represent diverse financial markets (Crypto, US Equities, Foreign Exchange, Gold, and PSX), engage in structured and constrained debate moderated by a supervisor agent, enforce strict risk control boundaries, and output actionable, explainable trading decisions with verified simulation metrics.

---

## Architecture Overview

```text
QUORUM/
├── frontend/             # TanStack Start, React 19, Tailwind CSS, shadcn/ui
├── backend/              # FastAPI, SQLAlchemy, Autonomous Agents, Supervisor & Risk
├── research/             # Quantitative study pipeline (Steps 01 - 07)
├── db/                   # SQLite schema & SQL migrations
└── docs/                 # CLO documentation (Analysis, Design, Agile, Meetings)
```

---

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_db.py
python scripts/import_knowledge.py

# Start FastAPI server:
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
cp .env.example .env
bun install # or npm install
bun run dev # or npm run dev
```

### 3. Running Research Pipeline
```bash
cd research
pip install -r requirements.txt
python 01_download_data.py
python 02_random_dummy_trades.py
python 03_roi_and_indicators.py
python 04_pattern_stats.py
python 05_rsi_strategy.py
python 06_make_report.py
python 07_profitable_pattern_histograms.py
```
