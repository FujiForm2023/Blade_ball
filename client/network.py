from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from main import Client

import pickle

class ServerConnectionManager():
    def __init__(self, client):
        self.client: Client = client
        self.logger = client.logger

    def start(self):
        reactor.connectTCP(self.client.host, self.client.port, ServerConnectionFactory(self.client, self.logger))
        reactor.run()

class ServerConnectionFactory(ClientFactory):
    def __init__(self, client, logger):
        self.client: Client = client
        self.logger = client.logger

    def startedConnecting(self, connector):
        self.logger.info('[Client:network:ServerConnectionFactory:startedConnecting] Started to connect.')

    def buildProtocol(self, addr):
        self.logger.info('[Client:network:ServerConnectionFactory:buildProtocol] Connected.')
        return ServerConnection(self.client, self.logger)

    def clientConnectionLost(self, connector, reason):
        self.logger.info('[Client:network:ServerConnectionFactory:clientConnectionLost] Lost connection.  Reason: %s', reason)

    def clientConnectionFailed(self, connector, reason):
        self.logger.info('[Client:network:ServerConnectionFactory:clientConnectionFailed] Connection failed. Reason: %s', reason)

class ServerConnection(Protocol):
    def __init__(self, client, logger):
        self.client: Client = client
        self.logger = client.logger

    def dataReceived(self, data: bytes):
        packet = pickle.loads(data)
        self.logger.info('[Client:network:ServerConnection:dataReceived] Received packet: %s', packet["type"])

    def connectionMade(self):
        self.transport.write(pickle.dumps({"type": "ServerboundJoin", "name": self.client.name}))
        self.logger.info('[Client:network:ServerConnection:connectionMade] Connection estdablished.')
