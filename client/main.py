import threading

from client.game import GameClient
from network import ServerConnectionManager

import structlog


class Client:
    def __init__(self, host="127.0.0.1", port=4536, name="test"):
        self.logger = structlog.get_logger()
        self.host = host
        self.port = port
        self.connection = ServerConnectionManager(self)
        self.game = None
        self.state = "INIT"
        self.name = name
        self.logger.info("[Client:main:init] Starting Blade Ball Client")

        self.start()

    def readSynced(self, synced: dict):
        self.game.parseSynced(synced)
        threading.Thread(target=self.game.main).start()

    def start(self):
        self.game = GameClient(self)
        self.connection.start()


if __name__ == "__main__":
    s = Client()
    s.start()
