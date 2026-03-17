# --- Build Stage ---
FROM python:3.10-slim as builder
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Copy only requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.10-slim
WORKDIR /app
# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
# Copy application code
COPY . .
# Set environment variables
ENV PYTHONUNBUFFERED=1
# Run the bot
CMD ["python", "bot.py"]
