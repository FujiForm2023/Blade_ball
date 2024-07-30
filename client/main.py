from network import ServerConnectionManager

class Client():
    def __init__(self, host, port=4536):
        self.host = host
        self.port = port
        self.connection = ServerConnectionManager(self)
        self.state = "INIT"

if __name__ == "__main__":
    s = Client()
    s.start()
