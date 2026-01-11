from prometheus_client import Counter, Summary

REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")
DOMAIN_PROCESSED_COUNTER = Counter(
    namespace="workers.domains",
    name="processed_domain_count",
    documentation="Count the number of domains that have been processed.",
    labelnames=["worker_id"],
)
DOMAIN_ADDED_COUNTER = Counter(
    namespace="workers.domains",
    name="added_domain_count",
    documentation="Count the number of domains that have been added.",
    labelnames=["worker_id"],
)
LINK_ADDED_COUNTER = Counter(
    namespace="workers.links",
    name="added_link_count",
    documentation="Count the number of links that have been added within a links worker.",
    labelnames=["worker_id"],
)
SELECTOR_LINK_ADDED_COUNTER = Counter(
    namespace="workers.selector",
    name="added_link_count",
    documentation="Count the number of links that have been added within a selector worker.",
    labelnames=["worker_id"],
)
SITEMAPS_LINK_ADDED_COUNTER = Counter(
    namespace="workers.sitemaps",
    name="added_link_count",
    documentation="Count the number of links that have been added within a sitemap worker.",
    labelnames=["worker_id"],
)
SITEMAPS_PROCESSED_COUNTER = Counter(
    namespace="workers.sitemaps",
    name="added_sitemap_count",
    documentation="Count the number of sitemaps that have been processed.",
    labelnames=["worker_id"],
)
