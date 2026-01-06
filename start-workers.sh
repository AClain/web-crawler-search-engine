#!/bin/bash
set -a
source .env
set +a

docker network inspect ${DOCKER_NETWORK:-monitoring} >/dev/null 2>&1 || \
    docker network create --driver bridge ${DOCKER_NETWORK:-monitoring}

docker compose build

docker compose up -d postgres rabbitmq prometheus grafana \
    worker-domains worker-sitemaps \
    worker-links worker-prioritizer \
    worker-router-low worker-router-medium \
    worker-router-high worker-selector-1 \
    worker-selector-2 worker-selector-3 \
    worker-selector-4 worker-selector-5 \
    --scale worker-domains=${NUM_DOMAINS_WORKERS:-2} \
    --scale worker-sitemaps=${NUM_SITEMAPS_WORKERS:-5} \
    --scale worker-links=${NUM_LINKS_WORKERS:-8} \
    --scale worker-prioritizer=${NUM_PRIORITIZER_WORKERS:-5} \
    --scale worker-router-low=${NUM_ROUTER_LOW_WORKER:-5} \
    --scale worker-router-medium=${NUM_ROUTER_MEDIUM_WORKER:-5} \
    --scale worker-router-high=${NUM_ROUTER_HIGH_WORKER:-5}
