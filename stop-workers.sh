#!/bin/bash
set -a
source .env
set +a

docker compose down worker-domains worker-sitemaps \
    worker-links worker-prioritizer \
    worker-router-low worker-router-medium \
    worker-router-high worker-selector-1 \
    worker-selector-2 worker-selector-3 \
    worker-selector-4 worker-selector-5