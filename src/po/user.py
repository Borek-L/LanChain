import time


class User:
    def __init__(self, host,port = 9000, nickname = None):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.now_connect = None
        self.last_heartbeat = time.time()