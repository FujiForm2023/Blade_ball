from typing_extensions import Dict
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
import pickle

class ConnectionManager(Factory):
    def __init__(self, server):
        self.server = server
        self.logger = server.logger
        self.clients = {}
        self.server.logger.info("[Server:network:ConnectionManager:init] Starting Connection Manager...")

    def start(self):
        reactor.listenTCP(self.server.port, ConnectionFactory(self.server, self.clients))
        self.logger.info("[Server:network:ConnectionManager:start] Listening for connections...")
        self.server.state = "OUT_OF_PLAY"
        reactor.run()

    def broadcast(self, packet: Dict):
        for client in self.clients.values():
            client.sendLine(pickle.dumps(packet))

class ConnectionFactory(Factory):
    def __init__(self, server, clients):
            self.clients = clients  # maps user names to Chat instances
            self.server = server

    def buildProtocol(self, addr):
        return ClientConnection(self.server, self.clients, addr)

class ClientConnection(LineReceiver):
    def __init__(self, server, clients, addr):
        self.server = server
        self.clients = clients
        self.addr = addr
        self.name: str = ""
        self.state = "INIT"

    def connectionMade(self):
        self.server.logger.info("[Server:network:ClientConnection:connectionMade] Incoming connection from %s!", self.addr)

    def connectionLost(self, reason):
        if self.name in self.clients:
            self.server.logger.info("[Server:network:ClientConnection:connectionLost] %s at %s lost connection.", self.name, self.addr)
            del self.clients[self.name]

    def lineReceived(self, line: bytes):
        if self.state == "INIT":
            self.initHandler(line)
        else:
            self.gameHandler(line)

    def initHandler(self, packet: bytes):
        decoded: dict = pickle.loads(packet)
        if decoded["type"] == "ServerboundJoin":
            self.name = decoded["name"]
            self.clients[self.name] = self

            if (self.server.state == "IN_PLAY"):
                self.sendLine(pickle.dumps({"type": "ClientboundWait"}))
                return
            elif (self.server.state == "OUT_OF_PLAY"):
                self.login()


        self.server.logger.info("[Server:network:ClientConnection:initHandler] %s joined the game with username %s.", self.addr, self.name.decode('utf-8'))

    def login(self):
        self.sendLine(pickle.dumps({"type": "ClientboundAccept"}))
        self.server.game.addPlayer(self)
        self.sendLine(pickle.dumps({"type": "ClientboundSync", "data": self.server.game.asdict()}))
        self.state = "PLAY"

    def gameHandler(self, packet: bytes):
