from pubsub import pub
import pygame


class GameClient:
    def __init__(self, client):
        self.client = client
        self.running = False
        self.width = 500
        self.height = 500

        self.ownPlayer: OwnClientPlayer | None = None
        self.players: dict[str, ClientPlayer] = {}
        self.ball: ClientPlayObject | None = None

        self.win = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Client")

        self.clock = pygame.time.Clock()

        pub.subscribe(self.updatePos, "updatePos")
        pub.subscribe(self.spawn, "spawn")
        pub.subscribe(self.despawn, "disconnect")

    def parseSynced(self, synced: dict[str, dict]):
        for name, player in synced["players"].items():
            if name == self.client.name:
                self.ownPlayer = OwnClientPlayer(player["x"], player["y"], player["size"], "#FFFF00", name)
            else:
                self.players[name] = ClientPlayer(player["x"], player["y"], player["size"], player["color"], name)

        self.ball = ClientPlayObject(synced["ball"]["x"], synced["ball"]["y"], synced["ball"]["size"],
                                     synced["ball"]["color"])

        self.client.logger.info("[Client:game:GameClient:parseSynced] Synced game state.")

    def spawn(self, name, x, y, size, color):
        self.players[name] = ClientPlayer(x, y, size, color, name)
        self.client.logger.info("[Client:game:GameClient:addPlayer] Added player %s.", name)

    def despawn(self, name):
        self.players.pop(name)
        self.client.logger.info("[Client:game:GameClient:despawn] Removed player %s.", name)

    def stop(self):
        self.client.logger.info("[Client:game:GameClient:stop] Stopping Client...")
        self.running = False

    def start(self):
        self.running = True
        self.client.logger.info("[Client:game:GameClient:start] Starting Client...")

    def tick(self):
        if self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pub.sendMessage("halt")

            self.ownPlayer.move()
            self.redrawWindow()
        else:
            self.client.logger.info("[Client:game:GameClient:main] Stopped Client.")
            pygame.quit()

    def redrawWindow(self):
        self.win.fill((255, 255, 255))

        self.ownPlayer.draw(self.win)
        self.ball.draw(self.win)
        for player in self.players.values():
            player.draw(self.win)

        pygame.display.update()

    def updatePos(self, name, x, y):
        self.players[name].x = x
        self.players[name].y = y
        self.players[name].rect = (x, y, self.players[name].size, self.players[name].size)


class ClientPlayObject:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.velocity = 3
        self.rect = (x, y, size, size)

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)


class ClientPlayer(ClientPlayObject):
    def __init__(self, x, y, size, color, name):
        super().__init__(x, y, size, color)
        self.name = name


class OwnClientPlayer(ClientPlayer):
    def move(self):
        keys = pygame.key.get_pressed()
        actuallyMoved = False

        if keys[pygame.K_LEFT]:
            self.x -= self.velocity
            actuallyMoved = True

        elif keys[pygame.K_RIGHT]:
            self.x += self.velocity
            actuallyMoved = True

        if keys[pygame.K_UP]:
            self.y -= self.velocity
            actuallyMoved = True

        elif keys[pygame.K_DOWN]:
            self.y += self.velocity
            actuallyMoved = True

        self.rect = (self.x, self.y, self.size, self.size)

        pub.sendMessage("move", x=self.x, y=self.y) if actuallyMoved else None
