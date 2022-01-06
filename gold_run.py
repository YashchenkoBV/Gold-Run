import pygame
import sys
import os


def load_image(name):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    return image


pygame.init()
FPS = 60
size = WIDTH, HEIGHT = 550, 500
clock = pygame.time.Clock()
tile_width = tile_height = 50
STEP = 3

tileset_1 = load_image('morning_adventures_tileset_16x16.png')
bush = pygame.Surface.subsurface(tileset_1, (112, 64, 16, 16))
ground_island = pygame.Surface.subsurface(tileset_1, (50, 48, 12, 16))
ground_row = pygame.Surface.subsurface(tileset_1, (0, 48, 48, 16))
spikes = pygame.Surface.subsurface(tileset_1, (80, 80, 16, 16))

tile_images = {
    'bush': pygame.transform.scale(bush, (40, 40)),
    'ground_island': pygame.transform.scale(ground_island, (50, 50)),
    'ground_block': pygame.transform.scale(ground_row, (150, 50)),
    'spikes': pygame.transform.scale(spikes, (50, 50))
}

all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
background_group = pygame.sprite.Group()


def start_screen():
    intro_text = ["Это временно"]

    fon = pygame.transform.scale(load_image('test_fon.png'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 370
    string_rendered = font.render(intro_text[0], True, pygame.Color('white'))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = text_coord
    intro_rect.x = 10
    text_coord += intro_rect.height
    screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class AnimatedPlayer(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(tile_width * x + 15, tile_height * y + 5)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


class BackGround(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(background_group)
        self.image = pygame.transform.scale(load_image('sky_background.png'), (2500, 550))
        self.rect = self.image.get_rect().move(0, 0)
        print('fogihb')


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    BackGround()
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                continue
            elif level[y][x] == '#':
                Tile('spikes', x, y)
            elif level[y][x] == '@':
                new_player = AnimatedPlayer(load_image('run.png'), 10, 1, x, y)
                print(x, y)
            elif level[y][x] == '_':
                Tile('ground_island', x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self, field_size):
        self.dx = 0
        self.dy = 0
        self.field_size = field_size

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        if obj.rect.x < -obj.rect.width:
            obj.rect.x += (self.field_size[0] + 1) * obj.rect.width
        if obj.rect.x >= (self.field_size[0]) * obj.rect.width:
            obj.rect.x += (self.field_size[0] + 1) * -obj.rect.width
        obj.rect.x -= 100

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)


screen = pygame.display.set_mode(size)
start_screen()
player, level_x, level_y = generate_level(load_level('lvl1.txt'))


def terminate():
    pygame.quit()
    sys.exit()


def jump():
    x_pos = player.rect.y
    global down_f
    if x_pos > ground - 65 and not down_f:
        x_pos -= 2  # v * t в секундах
    if x_pos <= ground - 65:
        down_f = True
        x_pos += 2  # v * t в секундах
    if down_f:
        x_pos += 2  # v * t в секундах
    if x_pos >= ground:
        global jump_f
        jump_f = False
    player.rect.y = x_pos


camera = Camera((level_x, level_y))
count = 0
player.cut_sheet(load_image('run.png'), 10, 1)
running = True
jump_f = False
while running:
    player.rect.x += STEP
    screen.blit(player.image, (player.rect.x, player.rect.y))
    if count == 6:
        player.update()
        count = 0
    for event in pygame.event.get():
        all_sprites.update()
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and player.rect.y >= 150:
                player.rect.y -= 150
            if event.key == pygame.K_DOWN and player.rect.y <= 400:
                player.rect.y += 150
            if event.key == pygame.K_SPACE and (player.rect.y == 105 or player.rect.y == 255 or player.rect.y == 405):
                ground = player.rect.y
                down_f = False
                jump_f = True
    if jump_f:
        jump()
    camera.update(player)

    for sprite in all_sprites:
        camera.apply(sprite)
    count += 1
    clock.tick(FPS)
    pygame.display.flip()
    screen.fill((0, 0, 0))
    background_group.draw(screen)
    tiles_group.draw(screen)
    player_group.draw(screen)

terminate()