# ── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies into a venv before copying the full source so that
# Docker can cache this layer when only application code changes.
RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy full source
COPY src/ src/
COPY config/ config/

# Lint gate — fail the build if ruff finds issues
RUN ruff check src/

# Test gate — run tests with coverage; threshold is 0 for now (raised in a later commit)
COPY tests/ tests/
RUN pytest tests/ --tb=short -q --cov=rita --cov-report=term-missing --cov-fail-under=0


# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only the pre-built venv from the builder stage
COPY --from=builder /build/venv /app/venv

# Copy application source and config
COPY src/ /app/src/
COPY config/ /app/config/

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Run as a non-root user
RUN useradd --uid 1000 --no-create-home --shell /sbin/nologin rita
USER rita

EXPOSE 8000

CMD ["uvicorn", "rita.main:app", "--host", "0.0.0.0", "--port", "8000"]
