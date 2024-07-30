import socket

class ConnectionManager:
    def __init__(server):
        server.logger.info("[Server:ConnectionManager] Starting Connection Manager...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((server.host, server.port))
        except socket.error as e:
            str(e)
        self.socket.listen(2)
        print("Waiting for a connection, Server Started")