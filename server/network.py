from typing_extensions import Dict
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from pubsub import pub

import struct
import time
import pickle


class ConnectionManager:
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
            client.sendPacket(packet)

    def broadcastExcept(self, packet: Dict, name: str):
        for client in self.clients.values():
            if client.name != name:
                client.sendPacket(packet)


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
        self.buffer = b''

    def connectionMade(self):
        self.server.logger.info("[Server:network:ClientConnection:connectionMade] Incoming connection from %s!",
                                self.addr)

    def connectionLost(self, reason):
        if self.name in self.clients:
            self.server.logger.info("[Server:network:ClientConnection:connectionLost] %s at %s lost connection.",
                                    self.name, self.addr)
            pub.sendMessage("despawn", name=self.name)

            disconnect = {"type": "ClientboundDisconnect", "name": self.name}
            self.server.connection.broadcastExcept(disconnect, self.name)
            self.server.logger.info(
                "[Server:network:ClientConnection:login] => All except %s: ClientboundDisconnect: %s",
                self.addr, disconnect)

            del self.clients[self.name]

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
                self.server.logger.info('[Server:network:ClientConnection:dataReceived] <- %s: %s: %s', self.addr,
                                        packet["type"], packet)
                self.parsePacket(packet)
            except pickle.UnpicklingError:
                break  # if unsuccessful, break the loop and wait for more data

    def parsePacket(self, packet: dict):
        if self.state == "INIT":
            self.initHandler(packet)
        else:
            self.gameHandler(packet)

    def initHandler(self, packet: dict):
        if packet["type"] == "ServerboundJoin":
            self.name = packet["name"]
            self.clients[self.name] = self

            if self.server.state == "IN_PLAY":
                self.sendPacket(pickle.dumps({"type": "ClientboundWait"}))
                self.server.logger.info(
                    "[Server:network:ClientConnection:initHandler] %s joined the game with username %s, waiting in the queue.",
                    self.addr, self.name)
                return
            elif self.server.state == "OUT_OF_PLAY":
                self.login()
                self.server.logger.info(
                    "[Server:network:ClientConnection:initHandler] %s joined the game with username %s.",
                    self.addr, self.name)

    def login(self):
        self.sendPacket({"type": "ClientboundAccept"})
        self.server.logger.info("[Server:network:ClientConnection:login] -> %s: ClientboundAccept", self.addr)
        pub.sendMessage("spawn", connection=self)
        self.sendPacket({"type": "ClientboundSync", "data": self.server.game.asdict()})
        self.server.logger.info("[Server:network:ClientConnection:login] -> %s: ClientboundSync: %s", self.addr,
                                self.server.game.asdict())

        spawn = {"type": "ClientboundSpawn", "name": self.name, "x": self.server.game.players[self.name].x,
                 "y": self.server.game.players[self.name].y, "size": self.server.game.players[self.name].size,
                 "color": self.server.game.players[self.name].color}
        self.server.connection.broadcastExcept(spawn, self.name)
        self.server.logger.info("[Server:network:ClientConnection:login] => All except %s: ClientboundSpawn: %s",
                                self.addr, spawn)

        self.state = "PLAY"

    def sendPacket(self, packet):
        data = pickle.dumps(packet)
        length = struct.pack('!I', len(data))
        self.transport.write(length + data)

    def gameHandler(self, packet: dict):
        self.server.logger.info("[Server:network:ClientConnection:gameHandler] -> %s: %s", self.name, packet["type"])
        if packet["type"] == "ServerboundMove":
            pub.sendMessage("move", name=self.name, x=packet["x"], y=packet["y"])
            self.server.connection.broadcastExcept(
                {"type": "ClientboundUpdatePos", "name": self.name, "x": packet["x"], "y": packet["y"]},
                self.name
            )
            self.server.logger.info("[Server:network:ClientConnection:gameHandler] -> %s: %s", self.name, packet)
