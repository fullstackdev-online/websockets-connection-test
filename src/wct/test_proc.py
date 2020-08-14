import os
import asyncio
import platform
from uuid import uuid4
import websockets
import json
import time
from datetime import datetime
from multiprocessing import Process
from .helper import LOGGER
import threading

WS_URL = os.getenv("WS_URL")
REQUESTS_INTERVAL_MS = int(os.getenv("REQUESTS_INTERVAL_MS", 0))
WORKER_ID = os.getenv("WORKER_ID", platform.node())
FORK_MODE = os.getenv("FORK_MODE", "proc")
MAX_REQUESTS = int(float(os.getenv("MAX_REQUESTS", 1)))


class TestProc:
    def __init__(self, data_q, tid, use_db, uri=None):
        self._data_q = data_q
        self._use_db = use_db
        self._max_requests = MAX_REQUESTS
        self._tid = tid
        self._worker_id = f"{WORKER_ID}-{self._tid}"
        if uri != None:
            self._uri = uri
        else:
            self._uri = WS_URL
        if FORK_MODE == "proc":
            self._proc = Process(target=self.run, args=())
            self._proc.start()
        elif FORK_MODE == "thread":
            self._test_thread = threading.Thread(
                target=self.run, args=())
            self._test_thread.start()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  # <----
        asyncio.ensure_future(self.send_request())
        loop.run_forever()

    async def send_request(self):
        connected = False
        async with websockets.connect(self._uri) as websocket:
            connected = True
            for _ in range(self._max_requests):
                uid = str(uuid4())
                payload = {
                    "action": "sendmessage",
                    "data": uid
                }
                start = time.time()
                await websocket.send(json.dumps(payload))
                response = await websocket.recv()
                mismatch = False
                if response != uid:
                    LOGGER.error(
                        f"response does not match request! Expected: {uid}, received: {response}")
                    mismatch = True
                duration = time.time() - start
                if self._use_db:
                    dp = {
                        "measurement": "wsRequestTime",
                        "tags": {
                            "worker": self._worker_id,
                            "mismatch": mismatch
                        },
                        "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                        "fields": {
                            "duration": duration
                        }
                    }
                    self._data_q.put([dp])
                else:
                    LOGGER.info(f"call duration: {duration}")
                if REQUESTS_INTERVAL_MS > 0:
                    await asyncio.sleep(REQUESTS_INTERVAL_MS/1000)
        if not connected:
            if self._use_db:
                dp = {
                    "measurement": "wsRequestTime",
                    "tags": {
                        "worker": self._worker_id,
                        "connect_failed": True
                    },
                    "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    "fields": {
                        "tid": self._tid
                    }
                }
                self._data_q.put([dp])
            else:
                LOGGER.info(f"failed to connect {self._worker_id}")
        LOGGER.info(f"worker {WORKER_ID}-{self._tid} finished")
