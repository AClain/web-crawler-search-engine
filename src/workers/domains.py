import logging
import os
from datetime import datetime
from urllib.parse import urlparse

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from src.database.engine import engine
from src.models.Domain import Domain
from src.prometheus_exporters import (
    DOMAIN_ADDED_COUNTER,
    DOMAIN_PROCESSED_COUNTER,
    REQUEST_TIME,
    WORKER_HEALTH_CHECK,
)
from src.repositories.DomainRepository import DomainRepository
from src.utils.parsers.robotsparser import (
    get_crawl_delay,
    get_robot_parser,
    get_sitemaps,
)

logger = logging.getLogger(__name__)

@REQUEST_TIME.time()
def process(new_domain_url: str, session: Session, channel: BlockingChannel) -> bool:
    was_added = False
    with session.begin():
        domain_repo = DomainRepository(session)
        parsed_url = urlparse(new_domain_url)
        if not parsed_url.netloc:
            logger.critical(f"Could not parse domain : {new_domain_url}.")
            return was_added

        domain = Domain(name=parsed_url.netloc, protocol=parsed_url.scheme)
        domain = domain_repo.upsert_one(domain)
        if domain is None:
            logger.critical(f"Could not upsert new domain : {new_domain_url}.")
            return was_added

        if domain.last_crawled_at is None:
            was_added = True
        domain.last_processed_at = datetime.now()
        domain.crawl_delay = get_crawl_delay(domain.name, domain.protocol)
        channel.basic_publish(
            exchange='',
            routing_key='links',
            body=f"{domain.protocol}://{domain.name}"
        )
        robot_parser = get_robot_parser(domain.name, domain.protocol)
        if robot_parser is None:
            domain.has_robots_txt = False
            return was_added

        domain.has_robots_txt = True
        for sitemap_url in get_sitemaps(domain.name, domain.protocol):
            channel.basic_publish(
                exchange='',
                routing_key='sitemaps',
                body=sitemap_url
            )
        return was_added

def main():
    worker_id = os.getenv("HOSTNAME", "unknown")
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))

    start_http_server(metrics_port)
    print(f'Started Prometheus metrics server on port {metrics_port}')

    connection = BlockingConnection(ConnectionParameters(
        host=os.getenv("RABBITMQ_HOSTNAME", "localhost"), 
        port=os.getenv("RABBITMQ_AMQP_FORWARD_PORT", 5672), 
        credentials=PlainCredentials(
            os.getenv("RABBITMQ_USERNAME", "guest"), 
            os.getenv("RABBITMQ_PASSWORD", "guest")
        )
    ))
    channel = connection.channel()

    channel.queue_declare(queue='domains')
    channel.queue_declare(queue='sitemaps')

    def work(ch, method, properties, body: bytes):
        domain_name = body.decode()
        print(f" [domains] [{worker_id}] Processing {domain_name}")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        try:
            with Session(engine) as session:
                was_added = process(domain_name, session, channel)
                if was_added:
                    DOMAIN_ADDED_COUNTER.labels(worker_id=worker_id).inc()
                DOMAIN_PROCESSED_COUNTER.labels(worker_id=worker_id).inc()
            print(f" [domains] [{worker_id}] Processed {domain_name}")
        except Exception as e:
            logger.critical(f"[{type(e).__name__}] - Lost {domain_name} inside a domains worker due to : {e}")

    channel.basic_consume(queue='domains', on_message_callback=work)

    try:
        channel.start_consuming()
        print(f' [domains] [{worker_id}] Waiting for domains to process. Press CTRL+C to exit')
        WORKER_HEALTH_CHECK.labels(worker_id=worker_id).set(1)
    except KeyboardInterrupt:
        print("Shutting down worker...")
        channel.stop_consuming()
        connection.close()
        WORKER_HEALTH_CHECK.labels(worker_id=worker_id).set(0)
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not start consuming due to : {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not run main() due to : {e}")