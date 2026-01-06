import logging
import os
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from src.database.engine import engine
from src.models.Domain import Domain
from src.models.Link import Link
from src.repositories.DomainRepository import DomainRepository
from src.repositories.LinkRepository import LinkRepository
from src.utils.parsers.robotsparser import is_allowed
from src.utils.parsers.urlparser import URLParser

logger = logging.getLogger(__name__)

def process(link_url: str, session: Session, channel: BlockingChannel):
    with session.begin():
        url_parser = URLParser(link_url)
        domain_name = url_parser.get_domain()
        domain_repo = DomainRepository(session)
        domain = domain_repo.find_one_by_name(domain_name)
        is_new_domain = False
        if domain is None:
            domain = Domain(
                name=domain_name,
                protocol=url_parser.get_scheme()
            )
            domain = domain_repo.upsert_one(domain)
            if domain is None:
                logger.critical(f"Could not upsert domain : {domain_name}.")
                return
            is_new_domain = True

        if is_new_domain and domain is not None:
            channel.basic_publish(
                exchange='',
                routing_key='domains',
                body=domain.name
            )

        link_repo = LinkRepository(session)
        pretty_link_url = url_parser.prettify()
        link = link_repo.find_one_by_url(pretty_link_url)
        if link is None:
            link = Link(url=pretty_link_url)
            link_repo.insert_one(link)

        if not is_allowed(domain.name, domain.protocol):
            link.last_crawled_at = datetime.now()
            return

        channel.basic_publish(
            exchange='',
            routing_key='prioritizer',
            body=str(link.id)
        )

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

    channel.queue_declare(queue='links')
    channel.queue_declare(queue='domains')
    channel.queue_declare(queue='prioritizer')

    def work(ch, method, properties, body: bytes):
        link_url = body.decode()
        print(f" [links] [{worker_id}] Processing link {link_url}")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        try:
            with Session(engine) as session:
                process(link_url, session, channel)
        except Exception as e:
            logger.critical(f"[{type(e).__name__}] - Lost {link_url} inside a links worker due to : {e}")

    channel.basic_consume(queue='links', on_message_callback=work)

    try:
        print(f" [links] [{worker_id}] Waiting for links to process. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down worker...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Happened while checking processes : {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not run main() due to : {e}")