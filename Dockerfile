# --- Stage 1: Builder ---
# This stage installs development tools and build dependencies.
FROM python:3.11-slim as builder

# Install build dependencies for pgvector (if needed) and general Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# This stage creates a lean, secure production image.
FROM python:3.11-slim as runtime

# Install runtime dependencies for asyncpg/psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY . .

# Ensure the app runs as the non-root user
RUN chown -R sentinel:sentinel /app
USER sentinel

# Expose the application port
EXPOSE 8080

# Run the FastAPI server using uvicorn
CMD ["python3", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
