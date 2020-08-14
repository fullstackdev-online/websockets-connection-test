import logging
import sys
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.DEBUG)

LOG_FORMAT = (
    "%(levelname) -10s %(name) -15s %(funcName) -5s %(lineno) -5d: %("
    "message)s")
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)