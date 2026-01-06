
from prometheus_client import Counter, Gauge, Summary

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
WORKER_HEALTH_CHECK = Gauge(
    namespace="workers",
    name="health_check",
    documentation="Is the worker up or down ?",
    labelnames=['worker_id']
)
DOMAIN_PROCESSED_COUNTER = Counter(
    namespace="workers",
    name="processed_domain_count",
    documentation="Count the number of domains that have been processed.",
    labelnames=['worker_id']
)
DOMAIN_ADDED_COUNTER = Counter(
    namespace="workers",
    name="added_domain_count",
    documentation="Count the number of domains that have been added.",
    labelnames=['worker_id']
)
SITEMAPS_PROCESSED_COUNTER = Counter(
    namespace="workers",
    name="processed_sitemap_count",
    documentation="Count the number of sitemaps that have been processed.",
    labelnames=['worker_id']
)