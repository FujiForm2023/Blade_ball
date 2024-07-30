from typing_extensions import Dict, List, overload
import pygame


class GameClient():
    def __init__(self, client, synced: Dict[str, Dict]):
        self.client = client
        self.running = False
        self.width = 500
        self.height = 500
        self.win = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Client")

        self.ownPlayer: OwnClientPlayer|None = None
        self.players: Dict[str, ClientPlayer] = {}
        self.ball: ClientPlayObject|None = None

    def parseSynced(self, synced: Dict[str, Dict]):
        for name, player in synced["players"].items():
            if name == self.client.name:
                self.ownPlayer = OwnClientPlayer(player["x"], player["y"], player["size"], player["color"], name)
            else:
                self.players[name] = ClientPlayer(player["x"], player["y"], player["size"], player["color"], name)

        self.ball = ClientPlayObject(synced["ball"]["x"], synced["ball"]["y"], synced["ball"]["size"], synced["ball"]["color"])

    def main(self):
        clock = pygame.time.Clock()

        while self.running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()

            self.ownPlayer.move()
            self.redrawWindow()

    def redrawWindow(self):
        self.win.fill((255,255,255))
        self.ownPlayer.draw(self.win)
        pygame.display.update()


class ClientPlayObject():
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.velocity = 3

class ClientPlayer(ClientPlayObject):
    def __init__(self, x, y, size, color, name):
        super().__init__(x, y, size, color)
        self.rect = (x, y, size, size)

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)

class OwnClientPlayer(ClientPlayer):
    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.x -= super().velocity

        if keys[pygame.K_RIGHT]:
            self.x += super().velocity

        if keys[pygame.K_UP]:
            self.y -= super().velocity

        if keys[pygame.K_DOWN]:
            self.y += super().velocity

        self.rect = (self.x, self.y, self.size, self.size)
