from network.network import ConnectionManager
import structlog

INSTANCE = None

class Server:
    def __init__(self, host="0.0.0.0", port=4536):
        INSTANCE = self
        self.host = host
        self.port = port
        self.logger = structlog.get_logger()
        self.logger.info("[Server] Starting Server at host %s port %s", host, port)
        self.connection = ConnectionManager(INSTANCE)

if __name__ == "__main__":
    Server()
