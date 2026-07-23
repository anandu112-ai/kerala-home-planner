# ── Stage 1: dependency builder ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed by some wheels (scikit-learn, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for Cloud Run security best-practice
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py         ./main.py
COPY services/       ./services/
COPY models/         ./models/

# Switch to non-root
USER appuser

# Cloud Run injects PORT at runtime (default 8080).
ENV PORT=8080

EXPOSE $PORT

# uvicorn reads $PORT at startup via the shell expansion below.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
