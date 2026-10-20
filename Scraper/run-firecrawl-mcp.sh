#!/bin/sh
# Launches the Firecrawl MCP server with FIRECRAWL_API_KEY loaded from .env
DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
. "$DIR/.env"
set +a
exec npx -y firecrawl-mcp
