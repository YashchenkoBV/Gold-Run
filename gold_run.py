import pygame
import sys
import os
from PIL import Image
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QMainWindow
from project_form1 import Ui_MainWindow1
from project_form2 import Ui_Form2

username = ''
fullname1 = os.path.join('data', 'user.db')
launch = False


def except_hook(cls, exception, traceback):  # Чтобы на ошибки было удобно смотреть
    sys.__excepthook__(cls, exception, traceback)


class StartWindow(QMainWindow, Ui_MainWindow1):  # Приветственное окно входа и регистрации
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.reg = None
        self.start = None
        self.registrationButton.clicked.connect(self.registration)
        self.enterButton.clicked.connect(self.entrance)

    def registration(self):  # Открывает форму регистрации
        self.reg = RegistrationWindow()
        self.reg.show()

    def entrance(self):  # Проверяет соответствие пароля имени пользователя и открывает основную форму

        global username, fullname1, launch
        con = sqlite3.connect(fullname1)
        cur = con.cursor()
        result = cur.execute("""SELECT password FROM user_info
                    WHERE name = ?""", (self.lineEdit.text(),)).fetchall()
        c = False
        for cort in result:
            if str(cort[0]) == self.lineEdit_2.text():
                c = True
                username = self.lineEdit.text()
                self.close()
                launch = True
                break
            else:
                continue
        if not c:
            self.lobbyError.setText('Неверное имя пользователя или пароль :(')
            self.lobbyError.setStyleSheet("QLabel { color: red}")


class RegistrationWindow(QWidget, Ui_Form2):  # Форма регистрации
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.readyButton.clicked.connect(self.run)

    def run(self):
        global fullname1
        con = sqlite3.connect(fullname1)  # Загружаем базу данных, в которую будем вносить имя и пароль
        cur = con.cursor()
        flag = True
        result = cur.execute("""SELECT name FROM user_info""").fetchall()
        for elem in result:
            if self.name.text() in elem:  # Имена пользователей не должны совпадать,
                # чтобы можно было хранить их проекты
                self.errorLabel.setText('Имя пользователя занято')
                self.errorLabel.setStyleSheet("QLabel { color: red}")
                flag = False
                break
        if flag:
            if self.name.text() and len(self.password.text()) >= 8:
                cur.execute("""INSERT INTO user_info(name,password, progress) VALUES (?,?, '1 0 0 0 0 0')""",
                            (self.name.text(), self.password.text()))
                con.commit()
                self.close()
            else:
                if not self.name.text():
                    self.errorLabel.setText('Вам следует ввести имя')
                    self.errorLabel.setStyleSheet("QLabel { color: red}")
                else:
                    self.errorLabel.setText('Пароль должен содержать не меньше 8 символов')
                    self.errorLabel.setStyleSheet("QLabel { color: red}")


def load_image(name):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


pygame.init()
# загрузка музыки
lose_sound = pygame.mixer.Sound('data/music/lose.ogg')
win_sound = pygame.mixer.Sound('data/music/win.ogg')
jump_sound = pygame.mixer.Sound('data/music/jump2.ogg')
coin_sound = pygame.mixer.Sound('data/music/coin.ogg')
coin_sound.set_volume(0.1)
jump_sound.set_volume(0.5)
FPS = 30
size = WIDTH, HEIGHT = 700, 800
clock = pygame.time.Clock()
tile_width = tile_height = 50
STEP = 5
ALIVE = True
WIN = False
cur_coins = 0
required_coins = [17, 30, 37, 47, 41]
ground_y = set()
tileset_1 = load_image('morning_adventures_tileset_16x16.png')
ground_island = pygame.Surface.subsurface(tileset_1, (50, 48, 12, 16))
ground_island = pygame.transform.scale(ground_island, (50, 50))
spikes = pygame.Surface.subsurface(tileset_1, (80, 80, 16, 16))
spikes = pygame.transform.scale(spikes, (50, 40))
levels_passed = []

player_width, player_height = Image.open('data/run2.png').size

cur_state = 'enter'
levels_lst = []
button_message_window_win = pygame.Rect(160, 390, 380, 100)


def load_progress():
    global fullname1
    levels_passed = []
    con = sqlite3.connect(fullname1)  # Загружаем базу данных, в которую будем вносить имя и пароль
    cur0 = con.cursor()
    result = cur0.execute("""SELECT progress FROM user_info WHERE name = ?""", (username,)).fetchall()
    print(result)
    for elem in result[0][0].split():
        if elem == '1':
            levels_passed.append(True)
        else:
            levels_passed.append(False)
    return levels_passed


def log():
    app = QApplication(sys.argv)
    login = StartWindow()
    login.show()
    sys.excepthook = except_hook
    app.exec()


def start_screen():
    global cur_state
    global screen, size
    global levels_passed
    screen = pygame.display.set_mode(size)
    fon = pygame.transform.scale(load_image('test_fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 40)
    string_rendered = font.render('Нажмите чтобы начать', True, (255, 255, 255))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = 620
    intro_rect.x = 80
    screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                write_progress()
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                log()
                levels_passed = load_progress()
                cur_state = 'menu'
                return
        pygame.display.flip()
        clock.tick(FPS)


all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
jumping_player_group = pygame.sprite.Group()
level_group = pygame.sprite.Group()
background_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()


# отрисовка текстур уровня
class Sprites(pygame.sprite.Sprite):
    def __init__(self, image, pos_x, pos_y, x_move=0, y_move=0, group=level_group):
        super().__init__(group, all_sprites)
        self.image = image
        self.rect = self.image.get_rect().move(tile_width * pos_x + x_move, tile_height * pos_y + y_move)
        self.mask = pygame.mask.from_surface(self.image)


# объекты с анимацией
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, x_move=0, y_move=0):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(tile_width * x + x_move, tile_height * y - y_move)

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


# фон
class BackGround(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(background_group)
        self.image = pygame.transform.scale(load_image('sky.png'), (700, 800))
        self.rect = self.image.get_rect().move(0, 0)


# oпределение текущего уровня
# собранных монет
class Count:
    def __init__(self, cur_coins, c, pos_x, pos_y):
        self.c = c
        self.font = pygame.font.Font(None, 50)
        self.text = self.font.render(f'{str(cur_coins)}/{required_coins[self.c - 1]}', True, (232, 215, 121))
        self.x, self.y = pos_x * tile_width + 10, pos_y * tile_height + 10

    def update(self):
        self.text = self.font.render(f'{str(cur_coins)}/{required_coins[self.c - 1]}', True, (232, 215, 121))


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def generate_level(level, c):
    new_player, chest, x, y = None, None, None, None
    BackGround()
    spikes_lst = []
    chests_lst = []
    coins_lst = []
    tiles_lst = []
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                continue
            elif level[y][x] == '#':
                spike = Sprites(pygame.transform.scale(spikes, (50, 50)), x, y, y_move=1)
                spikes_lst.append(spike)
            elif level[y][x] == 'C':
                chest = Sprites(pygame.transform.scale(load_image('chest.png'), (60, 50)), x, y)
                chests_lst.append(chest)
            elif level[y][x] == '@':
                new_player = AnimatedSprite(load_image('run1.png'), 32, 1, x, y, y_move=9)
            elif level[y][x] == '_':
                tile = Sprites(pygame.transform.scale(ground_island, (50, 50)), x, y)
                tiles_lst.append(tile)
                global ground_y, count
                ground_y.add(tile.rect.y - player_height)
            elif level[y][x] == '!':
                coin = AnimatedSprite(pygame.transform.scale(load_image('coin.png'), (560, 20)), 14, 1, x, y, 8, -15)
                coins_lst.append(coin)
            elif level[y][x] == 'T':
                stone = Sprites(pygame.transform.scale(load_image('tree.png'), (100, 150)), x, y, y_move=-100)
                spikes_lst.append(stone)
            elif level[y][x] == '*':
                bush = Sprites(pygame.transform.scale(load_image('bush.png'), (100, 40)), x, y, x_move=-50, y_move=10)
                spikes_lst.append(bush)
            elif level[y][x] == 't':
                tree = Sprites(pygame.transform.scale(load_image('tree.png'), (100, 150)), x, y, y_move=-100)
                chests_lst.append(tree)
            elif level[y][x] == 'K':
                count = Count(cur_coins, c, x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y, spikes_lst, chests_lst, coins_lst, tiles_lst, count


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
        obj.rect.x -= 200

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)


def terminate():
    pygame.quit()
    sys.exit()


def jump():
    global down_f, jump_f, player
    y_pos = jumping_player.rect.y
    jump_h = ground - 80
    if y_pos > jump_h and not down_f:
        y_pos -= 4  # v * t в секундах
    if y_pos <= jump_h:
        down_f = True
        y_pos += 4  # v * t в секундах
    if down_f:
        y_pos += 4  # v * t в секундах
    if y_pos >= ground:
        jump_f = False
        y_pos = ground
        player.rect.x, player.rect.y = jumping_player.rect.x, ground
    jumping_player.rect.y = y_pos
    jumping_player.rect.x += STEP


# запись прогресса игрока по уронвням
def write_progress():
    global fullname1, username
    con = sqlite3.connect(fullname1)  # Загружаем базу данных, в которую будем вносить имя и пароль
    cur0 = con.cursor()
    s = ''
    for elem in levels_passed:
        if elem:
            s += '1 '
        else:
            s += '0 '
    cur0.execute("""UPDATE user_info SET progress = ? WHERE name = ?""", (s, username))
    con.commit()


# окно выигрыша
def message_window_win():
    col = pygame.Color('#640933')
    pygame.draw.rect(screen, col, (150, 250, 400, 250), 0)
    font = pygame.font.Font(None, 35)
    string_rendered1 = font.render('Вы прошли уровень!', True, pygame.Color('yellow'))
    intro_rect = string_rendered1.get_rect()
    intro_rect.top = 280
    intro_rect.x = 220
    screen.blit(string_rendered1, intro_rect)
    string_rendered2 = font.render('Поздравляем!', True, pygame.Color('yellow'))
    intro_rect = string_rendered2.get_rect()
    intro_rect.top = 310
    intro_rect.x = 260
    screen.blit(string_rendered2, intro_rect)
    global button_message_window_win
    pygame.draw.rect(screen, pygame.Color('#ff7029'), button_message_window_win, 0)
    button_text = 'Вернуться в меню'
    font_button = pygame.font.Font(None, 60)
    string_rendered = font_button.render(button_text, True, pygame.Color('yellow'))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = 415
    intro_rect.x = 160
    screen.blit(string_rendered, intro_rect)
    global cur_coins
    coins_text = f'Собрано монет: {cur_coins}'
    coins_font = pygame.font.Font(None, 30)
    coins_rendered = coins_font.render(coins_text, True, pygame.Color('yellow'))
    coins_rect = coins_rendered.get_rect()
    coins_rect.top = 360
    coins_rect.x = 250
    screen.blit(coins_rendered, coins_rect)
    pygame.display.flip()
    clock.tick(FPS)


# окно проигрыша
def message_window_lose():
    col = pygame.Color('#640933')
    pygame.draw.rect(screen, col, (150, 250, 400, 250), 0)
    font = pygame.font.Font(None, 35)
    string_rendered1 = font.render('Вы проиграли!', True, pygame.Color('yellow'))
    intro_rect = string_rendered1.get_rect()
    intro_rect.top = 290
    intro_rect.x = 255
    screen.blit(string_rendered1, intro_rect)
    # В пайгеме каждую строку необходимо программировать по отдельности
    string_rendered2 = font.render('Попробуйте в другой раз!', True, pygame.Color('yellow'))
    intro_rect = string_rendered2.get_rect()
    intro_rect.top = 330
    intro_rect.x = 200
    screen.blit(string_rendered2, intro_rect)
    global button_message_window_win
    pygame.draw.rect(screen, pygame.Color('#ff7029'), button_message_window_win, 0)
    button_text = 'Вернуться в меню'
    font_button = pygame.font.Font(None, 60)
    string_rendered = font_button.render(button_text, True, pygame.Color('yellow'))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = 415
    intro_rect.x = 160
    screen.blit(string_rendered, intro_rect)


# Главное меню
# Пожалуй, самая сложная часть програмы
def main_menu():
    global cur_state
    global WIDTH, HEIGHT
    global cur_coins, username, fullname
    global player, level_x, level_y, spikes_lst, chests_lst, coins_lst
    pygame.display.set_caption('МЕНЮ')
    col1 = pygame.Color('#640933')
    pygame.draw.rect(screen, col1, (0, 0, WIDTH, HEIGHT), 0)
    main_font = pygame.font.Font(None, 120)
    title = main_font.render('Gold Run', True, pygame.Color('yellow'))
    title_rect = title.get_rect()
    title_rect.top = 20
    title_rect.x = 155
    screen.blit(title, title_rect)
    global levels_lst
    cyb = 155
    cyt = 185
    for i in range(5):
        button = pygame.Rect(10, cyb, 680, 100)
        if levels_passed[i]:
            pygame.draw.rect(screen, pygame.Color('#ff7029'), button, 0)
            color = pygame.Color('yellow')
        else:
            pygame.draw.rect(screen, pygame.Color('#999093'), button, 0)
            color = pygame.Color('#d79d41')
        levels_lst.append(button)
        button_font = pygame.font.Font(None, 60)
        button_text = button_font.render(f'{i + 1} уровень', True, color)
        button_rect = button_text.get_rect()
        button_rect.top = cyt
        button_rect.x = 230
        screen.blit(button_text, button_rect)
        cyb += 130
        cyt += 130
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                write_progress()
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                c = 0
                for elem in levels_lst:
                    c += 1
                    if elem.collidepoint(mouse_pos) and cur_state == 'menu' and levels_passed[c - 1]:
                        player, level_x, level_y, spikes_lst, chests_lst, coins_lst, tiles_lst, count = [None] * 8
                        cur_coins = 0
                        cur_state = 'game'
                        pygame.mixer.music.unload()
                        pygame.mixer.music.load('data/music/fon.ogg')
                        pygame.mixer.music.set_volume(0.4)
                        pygame.mixer.music.play(-1)
                        return generate_level(load_level(f'lvl{c}.txt'), c)

        pygame.display.flip()
        clock.tick(FPS)


screen = pygame.display.set_mode(size)
start_screen()
# создание уровня
player, level_x, level_y, spikes_lst, chests_lst, coins_lst, tiles_lst, count = main_menu()
jumping_player = Sprites(load_image('jump1.png'), player.rect.x, player.rect.y, group=jumping_player_group)
camera = Camera((level_x, level_y))
running = True
jump_f = False
win_sound_f = True
lose_sound_f = True
while running:
    if count.c >= 4:
        STEP = 6
    for event in pygame.event.get():
        if ALIVE:
            all_sprites.update()

        if event.type == pygame.QUIT:
            write_progress()
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if button_message_window_win.collidepoint(mouse_pos) and cur_state == 'win':
                cur_state = 'menu'
                ALIVE = True
                level_group.empty()
                coins_group.empty()
                player_group.empty()
                jumping_player_group.empty()
                player, level_x, level_y, spikes_lst, chests_lst, coins_lst, tiles_lst, count = main_menu()
                jumping_player = Sprites(load_image('jump1.png'), 0, 0, group=jumping_player_group)
                jump_f = False
                camera = Camera((level_x, level_y))
            elif button_message_window_win.collidepoint(mouse_pos) and cur_state == 'dead_inside':
                cur_state = 'menu'
                ALIVE = True
                # пересоздание уровня
                level_group.empty()
                coins_group.empty()
                player_group.empty()
                jumping_player_group.empty()
                player, level_x, level_y, spikes_lst, chests_lst, coins_lst, tiles_lst, count = main_menu()
                jumping_player = Sprites(load_image('jump1.png'), 0, 0, group=jumping_player_group)
                jump_f = False
                camera = Camera((level_x, level_y))

        elif event.type == pygame.KEYDOWN and ALIVE:
            # перемещения по дорожкам
            if event.key == pygame.K_UP and player.rect.y > sorted(list(ground_y))[0] and not jump_f:
                player.rect.y -= sorted(list(ground_y))[1] - sorted(list(ground_y))[0]
            if event.key == pygame.K_DOWN and player.rect.y < sorted(list(ground_y))[2] and not jump_f:
                player.rect.y += sorted(list(ground_y))[1] - sorted(list(ground_y))[0]
            # прыжок
            if event.key == pygame.K_SPACE:
                if player.rect.y in ground_y and not jump_f:
                    jump_sound.play()
                    ground = player.rect.y
                    jumping_player.rect.x, jumping_player.rect.y = player.rect.x, player.rect.y
                    down_f = False
                    jump_f = True

    # столкновения с монетами
    for coin in coins_lst:
        if not pygame.sprite.collide_mask(player, coin) and not pygame.sprite.collide_mask(jumping_player, coin):
            screen.blit(coin.image, (coin.rect.x, coin.rect.y))
            coin.update()
        else:
            del coins_lst[coins_lst.index(coin)]
            coin_sound.play()
            cur_coins += 1
            count.update()

    # столкновение с шипами и кустами
    for spike in spikes_lst:
        if pygame.sprite.collide_mask(player, spike) or pygame.sprite.collide_mask(jumping_player, spike):
            if ALIVE:
                lose_sound.play()
            if jump_f:
                cur = jumping_player
            else:
                cur = player
            ALIVE = False
            cur_state = 'dead_inside'
            screen.blit(cur.image, (cur.rect.x, cur.rect.y))
            message_window_lose()

    # столкновение с объектами-финишами
    for chest in chests_lst:
        if pygame.sprite.collide_mask(player, chest) or pygame.sprite.collide_mask(jumping_player, chest):
            # проверка количества монет
            if cur_coins >= required_coins[count.c - 1]:
                if ALIVE:
                    win_sound.play()
                ALIVE = False
                WIN = True
                cur_state = 'win'
                levels_passed[count.c] = True
                message_window_win()
            else:
                if ALIVE:
                    lose_sound.play()
                ALIVE = False
                cur_state = 'dead_inside'
                message_window_lose()

    if ALIVE:
        screen.blit(count.text, (count.x, count.y))
        for sprite in all_sprites:
            camera.apply(sprite)
        if jump_f:
            jump()
            screen.blit(jumping_player.image, (jumping_player.rect.x, jumping_player.rect.y))
            camera.update(jumping_player)
        else:
            screen.blit(player.image, (player.rect.x, player.rect.y))
            player.update()
            camera.update(player)
            player.rect.x += STEP
    else:
        pygame.mixer.music.pause()

    clock.tick(FPS)
    pygame.display.flip()
    screen.fill((0, 0, 0))
    background_group.draw(screen)
    level_group.draw(screen)
terminate()
