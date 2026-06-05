#!/usr/bin/env bash
# bootstrap.sh — First-time project setup for Memory Firewall
set -euo pipefail

echo "==> Checking Python version..."
python3 --version

echo "==> Installing Python dependencies..."
pip install -e ".[dev]" --quiet

echo "==> Copying .env.example to .env (if not present)..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    .env created — edit it to set your API keys."
else
  echo "    .env already exists, skipping."
fi

echo "==> Starting Docker services..."
docker compose -f infra/compose.yaml up -d --wait

echo "==> Applying Neo4j constraints..."
sleep 3  # give Neo4j a moment to be ready
docker compose -f infra/compose.yaml exec neo4j \
  cypher-shell -u neo4j -p password -f /var/lib/neo4j/import/constraints.cypher \
  2>/dev/null || echo "    (Neo4j constraint apply skipped — run manually if needed)"

echo ""
echo "✅  Bootstrap complete. Run 'make dev' to start the API server."
