import threading

from game import GameClient
from network import ServerConnectionManager
from pubsub import pub
from twisted.internet import task
import random

import structlog


class Client:
    def __init__(self, host="127.0.0.1", port=4536, name="test-0"):
        self.logger = structlog.get_logger()
        self.host = host
        self.port = port
        self.connection = ServerConnectionManager(self)
        self.game = None
        self.gameLoopTask = None
        self.state = "INIT"
        self.name = name
        self.logger.info("[Client:main:init] Starting Blade Ball Client as %s", name)

        pub.subscribe(self.halt, "halt")

        self.start()

    def readSynced(self, synced: dict):
        self.game.parseSynced(synced)
        self.game.start()
        self.gameLoopTask = task.LoopingCall(self.game.tick)
        self.gameLoopTask.start(1 / 60)

    def start(self):
        self.game = GameClient(self)
        self.connection.start()

    def halt(self):
        self.connection.stop()
        self.game.stop()
        self.logger.info("[Client:main:halt] Halting client.")


if __name__ == "__main__":
    name = f"test-{random.randint(0, 1000)}"
    s = Client(name=name)
    s.start()
