
import os
from argparse import ArgumentParser

from dotenv import load_dotenv
from pika import BlockingConnection, ConnectionParameters, PlainCredentials

load_dotenv()

def publish(queue_name: str, value: str):
    connection = BlockingConnection(ConnectionParameters(
        host='localhost', 
        port=os.getenv("RABBITMQ_AMQP_FORWARD_PORT", 5672), 
        credentials=PlainCredentials(
            os.getenv("RABBITMQ_USERNAME", "guest"), 
            os.getenv("RABBITMQ_PASSWORD", "guest")
        )
    ))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=value
    )

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "queue_name", 
        help="The name of the queue in which the value will be published.", 
        type=str
    )
    arg_parser.add_argument(
        "value", 
        help="The value to publish to the queue.", 
        type=str
    )
    args = arg_parser.parse_args()
    publish(args.queue_name, args.value)

if __name__ == "__main__":
    main()