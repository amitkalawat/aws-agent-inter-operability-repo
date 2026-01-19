# Amazon Rekognition MCP Server Dockerfile
# Provides image analysis capabilities via MCP protocol

FROM public.ecr.aws/docker/library/python:3.13-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system --compile-bytecode -r requirements.txt

FROM public.ecr.aws/docker/library/python:3.13-alpine

RUN apk add --no-cache ca-certificates

RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=app:app . .

USER app

ENV AWS_REGION=us-west-2
ENV MCP_SERVER_NAME=rekognition_mcp

HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

EXPOSE 8080

CMD ["python", "-m", "awslabs.amazon_rekognition_mcp_server"]
