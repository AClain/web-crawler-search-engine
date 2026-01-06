import logging
import os
import random
import uuid
from argparse import ArgumentParser

from pika import BlockingConnection, ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from src.database.engine import engine
from src.prometheus_exporters import (
    WORKER_HEALTH_CHECK,
)
from src.repositories.LinkRepository import LinkRepository
from src.vars import POOL_PREFIX

logger = logging.getLogger(__name__)

def process(link_id: uuid.UUID, session: Session, channel: BlockingChannel):
    with session.begin():
        link_repo = LinkRepository(session)
        link = link_repo.read_one(link_id)
        if link is None:
            logger.critical(f"Could not find link with ID {link_id}.")
            return
        pool_index = random.randint(1, 5)
        queue_name = f"{POOL_PREFIX}{pool_index}"
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=str(link.id)
        )

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "priority", 
        help="The priority for the workers to handle, either 'high', 'medium' or 'low'."
    )
    args = arg_parser.parse_args()
    if args.priority not in ["high", "medium", "low"]:
        print("Priority should be either 'high', 'medium' or 'low'.")
        return

    worker_id = os.getenv("HOSTNAME", "unknown")
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))

    start_http_server(metrics_port)
    print(f'Started Prometheus metrics server on port {metrics_port}')

    connection = BlockingConnection(ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    queue_name = f"{args.priority}_priority_links"
    channel.queue_declare(queue=queue_name)
    channel.queue_declare(queue='selector')
    for i in range(1, int(os.getenv("NUM_SELECTOR_WORKER", 10))+1):
        pool_queue_name = f"{POOL_PREFIX}{i}"
        channel.queue_declare(queue=pool_queue_name)

    def work(ch, method, properties, body: bytes):
        try:
            link_id = uuid.UUID(body.decode())
        except Exception as e:
            logger.critical(f"Could not parse UUID {body.decode()}. [{type(e).__name__}]: {e}")
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return
        print(f" [{queue_name}] Routing link {link_id}")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        try:
            with Session(engine) as session:
                process(link_id, session, channel)
        except Exception as e:
            logger.critical(f"[{type(e).__name__}] - Lost {link_id} inside {queue_name} worker due to : {e}")

    channel.basic_consume(queue=queue_name, on_message_callback=work)

    try:
        print(f' [{queue_name}] Waiting for links to route. To exit press CTRL+C')
        channel.start_consuming()
        WORKER_HEALTH_CHECK.labels(worker_id=worker_id).set(1)
    except KeyboardInterrupt:
        print("Shutting down worker...")
        channel.stop_consuming()
        connection.close()
        WORKER_HEALTH_CHECK.labels(worker_id=worker_id).set(0)
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Happened while checking processes : {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not run main() due to : {e}")