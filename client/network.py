import struct

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.protocols.basic import LineReceiver
from pubsub import pub

import pickle


class ServerConnectionManager:
    def __init__(self, client):
        self.client = client
        self.logger = client.logger

    def start(self):
        self.logger.info("[Client:network:ServerConnectionManager:start] Trying to connect to server at %s:%s...",
                         self.client.host, self.client.port)
        reactor.connectTCP(self.client.host, self.client.port, ServerConnectionFactory(self.client, self.logger))
        reactor.run()

    def stop(self):
        self.logger.info("[Client:network:ServerConnectionManager:stop] Stopping connection to server.")
        reactor.stop()


class ServerConnectionFactory(ClientFactory):
    def __init__(self, client, logger):
        self.client = client
        self.logger = client.logger

    def startedConnecting(self, connector):
        self.logger.info('[Client:network:ServerConnectionFactory:startedConnecting] Started to connect.')

    def buildProtocol(self, addr):
        self.logger.info('[Client:network:ServerConnectionFactory:buildProtocol] Connected.')
        return ServerConnection(self.client, self.logger)

    def clientConnectionLost(self, connector, reason):
        self.logger.info('[Client:network:ServerConnectionFactory:clientConnectionLost] Lost connection.  Reason: %s',
                         reason)

    def clientConnectionFailed(self, connector, reason):
        self.logger.info(
            '[Client:network:ServerConnectionFactory:clientConnectionFailed] Connection failed. Reason: %s', reason)
        exit(1)


class ServerConnection(LineReceiver):
    def __init__(self, client, logger):
        self.client = client
        self.logger = client.logger
        self.buffer = b''

        pub.subscribe(self.move, "move")

    def dataReceived(self, data: bytes):
        self.buffer += data  # add incoming data to the buffer
        while len(self.buffer) >= 4:  # ensure enough bytes for length (4 bytes for an integer)
            length = struct.unpack('!I', self.buffer[:4])[0]  # read length of packet
            if len(self.buffer) < 4 + length:  # ensure entire packet is in buffer
                break
            packet_data = self.buffer[4:4 + length]  # read packet data
            self.buffer = self.buffer[4 + length:]  # remove packet data from buffer
            try:
                packet = pickle.loads(packet_data)  # unpickle packet
                self.parsePacket(packet)
                self.logger.info('[Client:network:ServerConnection:dataReceived] <- %s: %s', packet["type"], packet)
            except pickle.UnpicklingError:
                break  # if unsuccessful, break the loop and wait for more data

    def parsePacket(self, packet: dict):
        if packet["type"] == "ClientboundSync":
            self.client.readSynced(packet["data"])
        elif packet["type"] == "ClientboundAccept":
            self.logger.info('[Client:network:ServerConnection:parsePacket] Server accepted connection.')
        elif packet["type"] == "ClientboundWait":
            self.logger.info(
                '[Client:network:ServerConnection:parsePacket] Server is waiting for the current game to end.')
        elif packet["type"] == "ClientboundUpdatePos":
            pub.sendMessage("updatePos", name=packet["name"], x=packet["x"], y=packet["y"])
        elif packet["type"] == "ClientboundSpawn":
            pub.sendMessage("spawn", name=packet["name"], x=packet["x"], y=packet["y"], size=packet["size"],
                            color=packet["color"])
        elif packet["type"] == "ClientboundDisconnect":
            pub.sendMessage("disconnect", name=packet["name"])
        else:
            self.logger.error('[Client:network:ServerConnection:parsePacket] Unknown packet type: %s', packet["type"])

    def move(self, x, y):
        self.sendPacket({"type": "ServerboundMove", "x": x, "y": y})

    def connectionMade(self):
        self.sendPacket({"type": "ServerboundJoin", "name": self.client.name})
        self.logger.info('[Client:network:ServerConnection:dataReceived] -> ServerboundJoin')
        self.logger.info('[Client:network:ServerConnection:connectionMade] Connection established.')

    def sendPacket(self, packet):
        data = pickle.dumps(packet)
        length = struct.pack('!I', len(data))
        self.transport.write(length + data)
