import logging
import os
import re
import time
import uuid
from argparse import ArgumentParser
from datetime import datetime
from urllib.parse import urlparse

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from requests.exceptions import ConnectionError
from sqlalchemy.orm import Session
from urllib3.exceptions import MaxRetryError

from src.database.engine import engine
from src.models.Link import Link
from src.models.LinkRelation import LinkRelation
from src.prometheus_exporters import SELECTOR_LINK_ADDED_COUNTER
from src.repositories.DomainRepository import DomainRepository
from src.repositories.LinkRelationRepository import LinkRelationRepository
from src.repositories.LinkRepository import LinkRepository
from src.utils.httpclient import HTTPClient
from src.utils.parsers.crawlparser import CrawlParser
from src.utils.parsers.urlparser import URLParser
from src.vars import MAX_CONTENT_CHARS, POOL_PREFIX

logger = logging.getLogger(__name__)

timeout_exceptions = (ConnectionError, MaxRetryError)

URL_PATTERN = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


def process(link_id: uuid.UUID, session: Session, channel: BlockingChannel):
    worker_id = os.getenv("HOSTNAME", "unknown")

    with session.begin():
        link_repo = LinkRepository(session)
        base_link = link_repo.read_one(link_id)
        if base_link is None:
            logger.critical(f"Could not find link with ID {link_id}.")
            return
        domain_repo = DomainRepository(session)
        url_parser = URLParser(base_link.url)
        domain_name = url_parser.get_domain()
        domain = domain_repo.find_one_by_name(domain_name)
        if domain is None:
            logger.critical(f"Could not find domain {domain_name}.")
            return

        if domain.last_crawled_at is not None:
            crawl_delay = domain.crawl_delay
            now = datetime.now()
            diff = int((now - domain.last_crawled_at).total_seconds())
            if diff < crawl_delay:
                time.sleep(crawl_delay - diff)

        try:
            http_client = HTTPClient()
            res = http_client.fetch(base_link.url)
        except timeout_exceptions as e:
            # TODO urllib3.exceptions.NameResolutionError => DNS, special queue for outdated domains ?
            logger.error(
                f"Fetching {base_link.url} resulted in [{type(e).__name__}]: {e}"
            )
            return

        domain.last_crawled_at = datetime.now()
        base_link.last_crawled_at = datetime.now()
        base_link.http_status = res.status_code
        if res.status_code >= 400 and res.status_code <= 500:
            logger.info(f"Skipping {base_link.url}. Status code {res.status_code}")
            return

        content_type = res.headers.get("Content-Type")
        base_link.content_type = content_type
        if content_type is None or "text/html" not in content_type:
            return

        crawl_parser = CrawlParser(res.text)
        body_content = crawl_parser.get_semantic_content()
        if body_content is not None:
            if len(body_content) > MAX_CONTENT_CHARS:
                body_content = body_content[:MAX_CONTENT_CHARS] + "...[truncated]"
            base_link.content = body_content
        hrefs = crawl_parser.get_safe_hrefs()
        if len(hrefs) < 1:
            return

        unsafe_hrefs = crawl_parser.get_unsafe_hrefs()
        for unsafe_href in unsafe_hrefs:
            if unsafe_href.startswith("//") or unsafe_href.startswith("/"):
                parsed_href = urlparse(unsafe_href)
                pretty_href = f"{domain.protocol}://{domain.name}/{parsed_href.path}"
                hrefs.append(pretty_href)

        link_relation_repo = LinkRelationRepository(session)
        for href in hrefs:
            href_match = re.match(URL_PATTERN, href)
            if href_match is None:
                logger.error(f"href did not match URL pattern: {href}")
                continue
            if len(href) > 512:
                continue
            link = link_repo.find_one_by_url(href)
            if link is not None:
                link_relation = link_relation_repo.find_one_by_relation(
                    link_id=base_link.id, has_link_id=link.id
                )
                if link_relation is not None:
                    continue
                link_relation = LinkRelation(link_id=base_link.id, has_link_id=link.id)
                link_relation_repo.insert_one(link_relation)
                continue

            link = Link(
                url=href,
                title=crawl_parser.get_title(),
                description=crawl_parser.get_description(),
                keywords=crawl_parser.get_keywords(),
                lang=crawl_parser.get_lang(),
            )
            link_repo.insert_one(link)
            SELECTOR_LINK_ADDED_COUNTER.labels(worker_id=worker_id).inc()
            link_relation = link_relation_repo.find_one_by_relation(
                link_id=base_link.id, has_link_id=link.id
            )
            link_relation = LinkRelation(link_id=base_link.id, has_link_id=link.id)
            link_relation_repo.insert_one(link_relation)
            channel.basic_publish(exchange="", routing_key="links", body=link.url)


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("index", help="The pool index for the worker to handle.")
    args = arg_parser.parse_args()

    metrics_port = int(os.getenv("METRICS_PORT", "8000"))

    start_http_server(metrics_port)
    print(f"Started Prometheus metrics server on port {metrics_port}")

    connection = BlockingConnection(
        ConnectionParameters(
            host=os.getenv("RABBITMQ_HOSTNAME", "localhost"),
            port=os.getenv("RABBITMQ_AMQP_FORWARD_PORT", 5672),
            credentials=PlainCredentials(
                os.getenv("RABBITMQ_USERNAME", "guest"),
                os.getenv("RABBITMQ_PASSWORD", "guest"),
            ),
        )
    )
    channel = connection.channel()

    queue_name = f"{POOL_PREFIX}{args.index}"
    channel.queue_declare(queue=queue_name)
    channel.queue_declare(queue="links")
    channel.queue_declare(queue="domains")

    def work(ch, method, properties, body: bytes):
        try:
            link_id = uuid.UUID(body.decode())
        except Exception as e:
            logger.critical(
                f"Could not parse UUID {body.decode()}. [{type(e).__name__}]: {e}"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        print(f" [{queue_name}] Crawling {link_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            with Session(engine) as session:
                process(link_id, session, channel)
        except Exception as e:
            logger.critical(
                f"[{type(e).__name__}] - Lost {link_id} inside {queue_name} worker due to : {e}"
            )

    channel.basic_consume(queue=queue_name, on_message_callback=work)

    try:
        print(f" [{queue_name}] Waiting for links to crawl. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down worker...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.critical(
            f"[{type(e).__name__}] - Could not start consuming due to : {e}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not run main() due to : {e}")
