from network import ConnectionManager
from game import GameServer
import structlog
import time


class Server:
    def __init__(self, host="0.0.0.0", port=4536):
        self.game = None
        self.connection = None
        self.startTime = time.time()
        self.host = host
        self.port = port
        self.logger = structlog.get_logger()
        self.logger.info("[Server:main:init] Starting Blade Ball Server at host %s port %s", host, port)
        self.state = "INIT"

        self.start()

    def start(self):
        self.connection = ConnectionManager(self)
        self.game = GameServer()
        self.logger.info("[Server:main:start] Server started in %s ms.",
                         round((time.time() - self.startTime) * 1000, 2))

        self.connection.start()


if __name__ == "__main__":
    s = Server()
    s.start()
