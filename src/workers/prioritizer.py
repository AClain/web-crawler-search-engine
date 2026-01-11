import logging
import os
import uuid

from pika import BlockingConnection, ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from src.database.engine import engine
from src.models.Link import ChangeFreq
from src.repositories.LinkRepository import LinkRepository

logger = logging.getLogger(__name__)


def process(link_id: uuid.UUID, session: Session, channel: BlockingChannel):
    with session.begin():
        link_repo = LinkRepository(session)
        link = link_repo.read_one(link_id)
        if link is None:
            return
        if link.change_freq == ChangeFreq.NEVER:
            return
        if link.change_freq in [ChangeFreq.YEARLY, ChangeFreq.MONTHLY]:
            channel.basic_publish(
                exchange="", routing_key="low_priority_links", body=str(link.id)
            )
            return
        elif link.change_freq in [ChangeFreq.WEEKLY]:
            channel.basic_publish(
                exchange="", routing_key="medium_priority_links", body=str(link.id)
            )
            return
        if link.priority >= 0.7:
            channel.basic_publish(
                exchange="", routing_key="high_priority_links", body=str(link.id)
            )
            return
        elif link.priority >= 0.5:
            channel.basic_publish(
                exchange="", routing_key="medium_priority_links", body=str(link.id)
            )
            return
        channel.basic_publish(
            exchange="", routing_key="low_priority_links", body=str(link.id)
        )
        return


def main():
    worker_id = os.getenv("HOSTNAME", "unknown")
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))

    start_http_server(metrics_port)
    print(f"Started Prometheus metrics server on port {metrics_port}")

    connection = BlockingConnection(ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.queue_declare(queue="prioritizer")
    channel.queue_declare(queue="low_priority_links")
    channel.queue_declare(queue="medium_priority_links")
    channel.queue_declare(queue="high_priority_links")

    def work(ch, method, properties, body: bytes):
        try:
            link_id = uuid.UUID(body.decode())
        except Exception as e:
            logger.critical(
                f"Could not parse UUID {body.decode()}. [{type(e).__name__}]: {e}"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f" [prioritizer] [{worker_id}] Prioritizing link {link_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            with Session(engine) as session:
                process(link_id, session, channel)
        except Exception as e:
            logger.critical(
                f"[{type(e).__name__}] - Lost {link_id} inside a prioritizer worker due to : {e}"
            )

    channel.basic_consume(queue="prioritizer", on_message_callback=work)

    try:
        print(
            " [prioritizer] [{worker_id}] Waiting for links to prioritize. To exit press CTRL+C"
        )
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down worker...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.critical(
            f"[{type(e).__name__}] - Happened while checking processes : {e}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[{type(e).__name__}] - Could not run main() due to : {e}")
