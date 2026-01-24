import logging
from pythonjsonlogger import json

def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = json.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)