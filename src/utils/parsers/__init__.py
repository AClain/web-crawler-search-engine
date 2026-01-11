import logging

logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG,
    filename="logs/logs.log",
    filemode="a",
    format="[%(asctime)s] - (%(name)s) - (%(levelname)s) - %(message)s",
)
