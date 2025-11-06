# Multi-stage build for production
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
# Firefox for Camoufox, Chromium for Selenium fallback, Xvfb for headless display
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    chromium \
    chromium-driver \
    firefox-esr \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Trigger browserforge data download as root (before switching to appuser)
RUN python3 init_browserforge.py || echo "Browserforge init skipped" && \
    chmod -R 755 /usr/local/lib/python3.10/site-packages/browserforge 2>/dev/null || true

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
