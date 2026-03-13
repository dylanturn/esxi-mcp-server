# Use official Python runtime as base image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy all source files needed for install
COPY requirements.txt setup.py ./
COPY esxi_mcp_server/ ./esxi_mcp_server/
COPY server.py .

# Install Python dependencies and the package using uv
RUN uv pip install --system --no-cache -r requirements.txt \
    && uv pip install --system --no-cache .

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set working directory
WORKDIR /app

# Install only runtime system dependencies (including bash for entrypoint script)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY server.py .
COPY esxi_mcp_server/ ./esxi_mcp_server/
COPY setup.py .
COPY config.yaml.sample .
COPY docker-entrypoint.sh .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/config \
    && chown -R mcpuser:mcpuser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

# Set entrypoint and default command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "esxi_mcp_server", "--config", "/app/config/config.yaml"]
