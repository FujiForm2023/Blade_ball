from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory

from main import Client

class ServerConnectionManager():
    def __init__(self, client):
        self.client: Client = client

    def start(self):
        reactor.connectTCP('localhost', 4536, ServerConnectionFactory())
        reactor.run()

class ServerConnectionFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return ServerConnection()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)

class ServerConnection(Protocol):
    def dataReceived(self, data: bytes):
        pass
