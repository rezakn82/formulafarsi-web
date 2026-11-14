#!/bin/bash
set -e
cd /var/www/formulafarsi
git pull
docker compose -f compose.yaml -f compose.prod.yaml up -d --build
docker image prune -f
echo "✅ Full Docker stack updated and restarted successfully!"
