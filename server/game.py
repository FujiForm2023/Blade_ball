from typing_extensions import Dict, List, overload
from pubsub import pub

import random


class GameServer:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.ball: Ball = Ball()

        pub.subscribe(self.movePlayer, "movePlayer")
        pub.subscribe(self.addPlayer, "spawn")
        pub.subscribe(self.removePlayer, "despawn")

    def addPlayer(self, connection):
        self.players[connection.name] = Player(random.randint(100, 400), random.randint(100, 400), 50, "#00FF00",
                                               connection)

    def removePlayer(self, name):
        self.players.pop(name)

    def movePlayer(self, name, x, y):
        self.players[name].x = x
        self.players[name].y = y

    def asdict(self):
        return {
            "players": {name: player.asdict() for name, player in self.players.items()},
            "ball": self.ball.asdict()
        }


class PlayObject:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.velocity = 3

    def asdict(self):
        return {
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": self.color
        }


class Player(PlayObject):
    def __init__(self, x, y, size, color, clientConnection):
        super().__init__(x, y, size, color)
        self.name = clientConnection.name
        self.clientConnection = clientConnection

    def asdict(self):
        return {
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": self.color,
            "name": self.name
        }


class Ball(PlayObject):
    def __init__(self, x=0, y=0):
        super().__init__(0, 0, 20, "#FF0000")
        self.target = None
