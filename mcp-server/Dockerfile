FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn[standard] sse-starlette

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Expose HTTP port
EXPOSE 3001

# Run MCP server (HTTP mode for remote connections)
CMD ["python", "-m", "src.http_server"]
