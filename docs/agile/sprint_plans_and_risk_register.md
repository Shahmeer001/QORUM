# QUORUM - Agile Project Management & Risk Register

## 1. Product Backlog & Sprints

### Sprint 1: Core Domain, Board & Data Adapters (Completed)
- Define domain models, enums, settings, and markets YAML.
- Implement memory board repository and visibility filtering.
- Implement synthetic data adapters (deterministic bull/bear regimes).
- Write unit tests for board, visibility, and data feeds.

### Sprint 2: Signal Pipeline & Research Integration (Completed)
- Implement RSI indicator calculation matching research methodology.
- Implement candle movement pattern labeler (`research/04_pattern_stats.py` equivalence).
- Implement `knowledge_loader.py` and knowledge import utility.
- Add test verifying 100% labeling parity between research and backend.

### Sprint 3: Autonomous Agents, Supervisor & Risk (Completed)
- Create `MarketAgent` and `RuleBrain`.
- Implement challenge/reply logic and debate turn coordinator.
- Build supervisor consensus algorithm and agent accuracy tracker.
- Build risk filter with volatility and drawdown veto rules.

### Sprint 4: Simulator, Modes & Database (Completed)
- Build deterministic trade simulator and equity curve generator.
- Implement Single, Silent, and Debate modes.
- Implement SQLite tables and repositories with seed scripts.

### Sprint 5: REST API & Frontend Integration (Completed)
- Expose `/markets`, `/sessions`, and `/compare` endpoints.
- Update frontend API client and session store.
- Connect all UI pages to live backend with offline fallback.

---

## 2. Risk Register

| Risk ID | Description | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|---|
| R-1 | Look-ahead bias across markets | High | Med | Centralized `visibility.py` policy applied on all board reads. |
| R-2 | Agent debate deadlock / infinite loop | Med | Low | Strict turn cap (`max_turns <= 3`) enforced by supervisor. |
| R-3 | Synthetic vs real data discrepancies | Med | Med | Common `Candle` domain model and standardized adapter protocol. |
| R-4 | Network / API failure in frontend | Low | Med | Dual-mode frontend: attempts API call, falls back gracefully to local state. |
