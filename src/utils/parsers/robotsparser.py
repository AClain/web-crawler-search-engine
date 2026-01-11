import logging
from functools import lru_cache
from typing import Optional
from urllib.robotparser import RobotFileParser

from src.utils.httpclient import HTTPClient, get_user_agent
from src.vars import DEFAULT_CRAWL_DELAY

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1000)
def get_robot_parser(domain_name: str, protocol: str) -> Optional[RobotFileParser]:
    try:
        robots_url = f"{protocol}://{domain_name}/robots.txt"
        http_client = HTTPClient()
        res = http_client.fetch(robots_url)
    except Exception as e:
        logger.error(f"Fetching {robots_url} resulted in [{type(e).__name__}]: {e}")
        return None

    if res.status_code != 200:
        return None

    robot_parser = RobotFileParser()
    robot_parser.parse(res.text.splitlines())
    return robot_parser


@lru_cache(maxsize=1000)
def is_allowed(domain_name: str, protocol: str):
    robot_parser = get_robot_parser(domain_name, protocol)
    if robot_parser is None:
        return True

    return robot_parser.can_fetch(get_user_agent(), f"{protocol}://{domain_name}")


@lru_cache(maxsize=1000)
def get_crawl_delay(domain_name: str, protocol: str):
    robot_parser = get_robot_parser(domain_name, protocol)

    if robot_parser is None:
        return DEFAULT_CRAWL_DELAY

    crawl_delay = robot_parser.crawl_delay(get_user_agent())
    if crawl_delay is None:
        return DEFAULT_CRAWL_DELAY
    if int(crawl_delay) > 10:
        return 10
    if int(crawl_delay) < 0:
        return DEFAULT_CRAWL_DELAY
    return int(crawl_delay)


@lru_cache(maxsize=1000)
def get_sitemaps(domain_name: str, protocol: str):
    robot_parser = get_robot_parser(domain_name, protocol)

    if robot_parser is None:
        return []

    sitemap_urls = robot_parser.site_maps()
    return sitemap_urls if sitemap_urls is not None else []
