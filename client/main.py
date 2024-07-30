from network import ServerConnectionManager

import structlog

class Client():
    def __init__(self, host, port=4536):
        self.host = host
        self.port = port
        self.connection = ServerConnectionManager(self)
        self.game = None
        self.state = "INIT"
        self.name = ""

        self.start()

    def start(self):
        self.connection.start()

if __name__ == "__main__":
    s = Client()
    s.start()
