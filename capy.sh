#!/bin/bash
set -a
source .env
set +a

mode=""
services=false
workers=false
db_size=false

case "$1" in
    "start")
        mode="start" ;;

    "stop")
        mode="stop" ;;

    "db_size")
        db_size=true ;;
esac

if [ $db_size = true ]; then
    docker exec -i $POSTGRES_CONTAINER_NAME psql postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DATABASE <<EOF
\l+ $POSTGRES_DATABASE
EOF
fi

case "$2" in
    "all")
        services=true
        workers=true ;;

    "workers")
        workers=true ;;

    "services")
        services=true ;;
esac

if [ $mode = "start" ]; then
    if [ $services = true ]; then
        docker network inspect ${DOCKER_NETWORK:-monitoring} >/dev/null 2>&1 || \
            docker network create --driver bridge ${DOCKER_NETWORK:-monitoring}

        docker compose up -d postgres rabbitmq prometheus grafana
    fi

    if [ $workers = true ]; then
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
    fi
fi

if [ $mode = "stop" ]; then
    if [ $services = true ]; then
        docker compose down postgres rabbitmq prometheus grafana
    fi

    if [ $workers = true ]; then
        docker compose down worker-domains worker-sitemaps \
            worker-links worker-prioritizer \
            worker-router-low worker-router-medium \
            worker-router-high worker-selector-1 \
            worker-selector-2 worker-selector-3 \
            worker-selector-4 worker-selector-5
    fi
fi