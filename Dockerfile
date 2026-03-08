# Use official Python runtime as base image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and setup files
COPY requirements.txt setup.py ./

# Copy application package (needed for pip install -e .)
COPY esxi_mcp_server/ ./esxi_mcp_server/
COPY server.py .

# Install Python dependencies and the package itself
RUN pip install --no-cache-dir --user -r requirements.txt \
    && pip install --no-cache-dir --user -e .

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
COPY --from=builder /root/.local /home/mcpuser/.local

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
ENV PATH=/home/mcpuser/.local/bin:$PATH
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
