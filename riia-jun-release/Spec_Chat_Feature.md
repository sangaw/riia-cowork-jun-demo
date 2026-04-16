 Chat Feature — Current Structure

  It's fully local, no Claude/Anthropic API calls at runtime.

  How it works (3-layer pipeline):

  1. Intent Classification (src/rita/core/classifier.py)
    - Uses sentence-transformers/all-MiniLM-L6-v2 — a local embedding model
    - 20 fixed investment intents, each with seed phrases
    - Cosine similarity between the user query and seed embeddings determines the best-matching intent
    - Confidence threshold: 0.42 (below = low-confidence fallback)
    - Model is lazy-loaded once, then cached in memory (_model global)
  2. Data Calculations (dispatch() in classifier.py)
    - Once the intent is classified, a deterministic handler runs against live OHLCV data
    - Handlers: market_sentiment, strategy_recommendation, return_estimates, stress_scenarios, performance_feedback, portfolio_comparison
    - All responses are computed from nifty_merged.csv + indicator calculations — no LLM generation
  3. Response Caching (rest_api.py:94)
    - The market signals DataFrame is cached (_market_signals_cache) and only recomputed when the CSV file's mtime changes
    - This is data caching, not LLM response caching

  Entry points:

  - POST /api/v1/chat/warmup — pre-warms the SentenceTransformer (called when chat UI opens)
  - POST /api/v1/chat — classifies query + dispatches handler + logs to chat_monitor.csv

  ---