import os
from multiprocessing import JoinableQueue
from wct.test_proc import TestProc
from wct.db import DataPusher

MAX_PROC = int(os.getenv("MAX_PROC", 1))
USE_DB = bool(os.getenv("USE_DB", False))


if __name__ == "__main__":
    data_q = None
    if USE_DB:
        dp = DataPusher()
        data_q = dp.get_mq()
    for tid in range(MAX_PROC):
        TestProc(data_q, tid, USE_DB)
