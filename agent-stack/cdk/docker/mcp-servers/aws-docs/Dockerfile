# AWS Documentation MCP Server Dockerfile
# Provides AWS documentation search capabilities via MCP protocol

FROM public.ecr.aws/docker/library/python:3.13-alpine AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --compile-bytecode -r requirements.txt

# Runtime stage
FROM public.ecr.aws/docker/library/python:3.13-alpine

# Install runtime dependencies
RUN apk add --no-cache ca-certificates

# Create non-root user
RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=app:app . .

USER app

# Environment configuration
ENV AWS_REGION=us-west-2
ENV MCP_SERVER_NAME=aws_docs_mcp

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

EXPOSE 8080

# Entry point for MCP server
CMD ["python", "-m", "awslabs.aws_documentation_mcp_server"]
