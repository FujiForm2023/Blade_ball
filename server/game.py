from typing_extensions import Dict, List, overload
import random

class GameServer():
    def __init__(self):
        self.players : Dict[str, Player] = {}
        self.ball: Ball = Ball()

    def addPlayer(self, clientConnection):
        self.players[clientConnection.name] = Player(random.randint(200, 300), random.randint(200, 300), 50, "#00FF00", clientConnection)

    def asdict(self):
        return {
            "players": {name: player.asdict() for name, player in self.players.items()},
            "ball": self.ball.asdict()
        }

class PlayObject():
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
        super().__init__(0, 0, 30, "#FF0000")
        self.target = None
