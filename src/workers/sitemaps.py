import logging
import os

from pika import BlockingConnection, ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from src.database.engine import engine
from src.prometheus_exporters import SITEMAPS_PROCESSED_COUNTER, WORKER_HEALTH_CHECK
from src.repositories.LinkRepository import LinkRepository
from src.utils.httpclient import HTTPClient
from src.utils.parsers.sitemapparser import SitemapParser
from src.utils.parsers.urlparser import URLParser

logger = logging.getLogger(__name__)

def process(sitemap_url: str, session: Session, channel: BlockingChannel):
    http_client = HTTPClient()
    
    try:
        http_client = HTTPClient()
        res = http_client.fetch(sitemap_url)
    except Exception as e:
        logger.error(f"Fetching {sitemap_url} resulted in [{type(e).__name__}]: {e}")
        return

    parser = SitemapParser(res.text)
    for index_url in parser.get_indexes():
        channel.basic_publish(
            exchange='',
                routing_key='sitemaps',
                body=index_url
            )
    for link in parser.get_links():
        if len(link.url) > 512:
            continue
        url_parser = URLParser(link.url)
        pretty_url = url_parser.prettify()
        link_repo = LinkRepository(session)
        link_db = link_repo.find_one_by_url(pretty_url)
        if link_db is None:
            link_repo.insert_one(link)
        channel.basic_publish(
            exchange='',
            routing_key='links',
            body=pretty_url
        )

def main():
    worker_id = os.getenv("HOSTNAME", "unknown")
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))

    start_http_server(metrics_port)
    print(f'Started Prometheus metrics server on port {metrics_port}')

    connection = BlockingConnection(ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='sitemaps')
    channel.queue_declare(queue='links')

    def work(ch, method, properties, body: bytes):
        sitemap_url = body.decode()
        print(f" [x] Processing sitemap {sitemap_url}")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        try:
            with Session(engine) as session:
                process(sitemap_url, session, channel)
                SITEMAPS_PROCESSED_COUNTER.labels(worker_id=worker_id).inc()
        except Exception as e:
            logger.critical(f"[{type(e).__name__}] - Lost {sitemap_url} inside a sitemap worker due to : {e}")

    channel.basic_consume(queue='sitemaps', on_message_callback=work)

    try:
        channel.start_consuming()
        print(f' [sitemaps] [{worker_id}] Waiting for sitemaps to process. To exit press CTRL+C')
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