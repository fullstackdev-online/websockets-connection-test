import os
from multiprocessing import JoinableQueue, Process
from influxdb import InfluxDBClient
from .helper import LOGGER

DB_NAME = os.getenv("INFLUX_DATABASE", "db")
DB_HOST = os.getenv("INFLUX_HOST", "localhost")
DB_PORT = int(os.getenv("INFLUX_PORT", 8086))
DB_USER = os.getenv("INFLUX_USERNAME", "")
DB_PASSWORD = os.getenv("INFLUX_PASSWORD", "")


class DataPusher:
    def __init__(self) -> None:
        LOGGER.info("intialiasing DB pusher")
        self._mq = JoinableQueue()
        self._client = None
        self._init_connection()
        self._proc = Process(target=self.run, args=())
        self._proc.start()

    def get_mq(self):
        return self._mq

    def get_proc(self):
        return self._proc

    def push_meter_values(self, payload):
        return self._client.write_points(payload)

    def _init_connection(self):
        self._client = InfluxDBClient(
            host=DB_HOST, port=DB_PORT,
            username=DB_USER, password=DB_PASSWORD)
        try:
            self._client.switch_database(DB_NAME)
        except Exception as e:
            LOGGER.error(f"failed to switch database, {e}, trying to create")
            self._client.create_database(DB_NAME)
            self._client.switch_database(DB_NAME)

    def run(self):
        LOGGER.info("started DB pusher process")
        while True:
            payload = self._mq.get()
            LOGGER.debug(f"got new payload for db pusher {payload}")
            self.push_meter_values(payload)
