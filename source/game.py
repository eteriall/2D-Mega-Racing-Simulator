import json
import math
import os
import random
import sys
import time
from pygame import gfxdraw

import pygame
from Box2D import b2WheelJointDef, b2Vec2, b2FixtureDef, b2BodyDef, b2PolygonShape, b2ContactListener
from Box2D.b2 import world, polygonShape, circleShape, staticBody, dynamicBody
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame_widgets import Button as BrokenButton

pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.mixer.music.set_volume(0.05)

"""Константы экрана и камеры"""
PPM = 23
TARGET_FPS = 100
TIME_STEP = 1.0 / TARGET_FPS
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
delta_x, delta_y = 0, 0
DEBUG = False


def shake():
    """Генератор значений для встряхивания камеры"""
    s = -1
    for _ in range(0, 5):
        for x in range(0, 20, 10):
            yield (0, (x / 10 * s))
        for x in range(20, 0, -10):
            yield (0, x / 10 * s)
        s *= -1
    while True:
        yield (0, 0)


def invert(*args):
    """Инвертируем список координат по y"""
    return list(map(lambda x: (x[0], SCREEN_HEIGHT - x[1]), args))


def rotate_image(image, pos, originPos, angle):
    """Вращение картинки"""
    w, h = image.get_size()
    box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    pivot = pygame.math.Vector2(originPos[0], -originPos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot
    origin = (pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1])
    rotated_image = pygame.transform.rotate(image, angle)
    return rotated_image, origin


def load_image(name, colorkey=None, size=None):
    """Загрузка картинки"""
    fullname = os.path.join('sprites', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if size is not None:
        image = pygame.transform.scale(image, size)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def my_draw_polygon(poly, body, fixture):
    global delta_y, delta_x
    """Функция отрисовки полигональных тел"""
    if not DEBUG and body.userData in ("left_wheel", "right_wheel", "car_body", "border"):
        return

    vertices = [(body.transform * v) * PPM for v in poly.vertices]
    vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
    vertices = [camera.apply_coords(x) for x in vertices]
    vertices = list(map(lambda x: (int(x[0]), int(x[1])), vertices))

    if not DEBUG:
        # Отрисовка залитого тела
        try:
            if body.userData == "t":
                pygame.gfxdraw.textured_polygon(screen, vertices, GROUND_TEXTURE, -int(delta_x) % 512,
                                                -int(delta_y) % 512)
                x1, y1, x2, y2 = list(map(int, vertices[1] + vertices[2]))
                """pygame.gfxdraw.aapolygon(screen, ((x1, y1), (x2, y2), (x2, y2 + 50), (x1, y1 + 50)), (255, 0, 0))"""
                pygame.draw.line(screen, colors["l"], (x1, y1), (x2, y2), 10)
            else:
                pygame.gfxdraw.filled_polygon(screen, vertices, colors[body.userData])
        except Exception as e:
            pass
    else:
        try:
            gfxdraw.aapolygon(screen, vertices, colors[body.userData])
        except KeyError:
            gfxdraw.filled_polygon(screen, vertices, (255, 0, 255))


def my_draw_circle(circle, body, fixture):
    """Функция отрисовки круглых тел"""
    if not DEBUG and body.userData in ("left_wheel", "right_wheel", "left", "right"):
        return
    position = body.transform * circle.pos * PPM
    position = (position[0], SCREEN_HEIGHT - position[1])
    position = list(map(int, camera.apply_coords(position)))

    try:
        gfxdraw.aacircle(screen, *position, int(circle.radius * PPM), colors[body.userData])
        gfxdraw.filled_circle(screen, *position, int(circle.radius * PPM), colors[body.userData])
    except KeyError:
        if DEBUG:
            try:
                gfxdraw.aacircle(screen, *position, int(circle.radius * PPM), (255, 0, 255))
            except OverflowError:
                pygame.draw.circle(screen, (255, 0, 255), position, int(circle.radius * PPM), 2)


def rotate_around_point(xy, degrees, origin=(0, 0)):
    """Функция, вращающая координаты относительно origin-а"""
    radians = math.radians(degrees)
    x, y = xy
    offset_x, offset_y = origin
    adjusted_x = (x - offset_x)
    adjusted_y = (y - offset_y)
    cos_rad = math.cos(radians)
    sin_rad = math.sin(radians)
    qx = offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y
    qy = offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y

    return qx, qy


class Button(BrokenButton):
    def __init__(self, win, x, y, width, height, **kwargs):
        """Я переписал класс кнопки из модуля pygame_widgets"""
        self.userData = kwargs.get('userData', None)
        kwargs["font"] = kwargs.get('font', sf_pro_font_36)
        super(Button, self).__init__(win, x, y, width, height, **kwargs)

    def listen(self, events):
        """Мне не понравилось, как отрабатывает функция прослушки событий поэтому я её переписал."""
        if not self.hidden:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.contains(*event.pos):
                        self.onClick(self)
                        button_sound.play()
            x, y = pygame.mouse.get_pos()
            if self.contains(x, y) and pygame.mouse.get_pressed(3)[0]:
                self.colour = self.pressedColour
            elif self.contains(x, y):
                self.colour = self.hoverColour
            else:
                self.colour = self.inactiveColour


class CategoryButton:
    bg_color = (0, 0, 0)
    inactive = (100, 100, 100)
    pressed = (160, 160, 160)
    textColour = (255, 255, 255)

    def __init__(self, xy, wh, text, onClick, image=None, radius=20):
        """Кнопка с задним фоном. Используется в меню."""

        self.size = (xy, wh)
        self.userData = ''
        self.radius = radius
        x, y = xy
        w, h = wh
        self.onClick = onClick
        self.back = Button(
            screen, x, y, w, h, text='',
            inactiveColour=self.bg_color,
            pressedColour=self.bg_color,
            image=image,
            radius=radius,
            imageVAlign="bottom"
        )

        margin = 20
        x, y = x + margin, y + h - 80 - margin
        w, h = w - 2 * margin, 80
        self.front = Button(
            screen, x, y, w, h, text=text,
            inactiveColour=self.inactive,
            pressedColour=self.pressed,
            radius=radius,
            textColour=self.textColour,
            onClick=onClick,
            fontSize=48,
        )

    def set_content(self, text='', image=None, backText='',
                    fontSizeBack=200, fontSizeFront=48,
                    onClick=None, userData=None):
        """Меняем содержимое кнопки"""
        xy, wh = self.size
        x, y = xy
        w, h = wh

        self.back = Button(
            screen, x, y, w, h, text=backText,
            inactiveColour=self.bg_color,
            pressedColour=self.bg_color,
            textColour=self.textColour,
            fontSize=fontSizeBack,
            radius=self.radius,
            image=image
        )

        margin = 20
        x, y = x + margin, y + h - 80 - margin
        w, h = w - 2 * margin, 80
        self.front = Button(
            screen, x, y, w, h, text=text,
            inactiveColour=self.inactive,
            pressedColour=self.pressed,
            radius=self.radius,
            textColour=self.textColour,
            onClick=self.onClick if onClick is None else onClick,
            fontSize=fontSizeFront,
            userData=userData
        )

    def draw(self):
        """Отрисовка кнопки"""
        self.back.draw()
        self.front.draw()

    def listen(self, events):
        """Прослушка событий"""
        self.front.listen(events)


class MainMenu:
    def __init__(self):
        """Главное меню"""

        self.BACKGROUND_COLOR = (29, 29, 29)

        inactive = (100, 100, 100)
        pressed = (160, 160, 160)
        textColour = (255, 255, 255)

        self.world_button = Button(
            screen, 262, 832, 319, 106, text='World',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.choose_level_screen,
            textColour=textColour,

        )
        self.vehicle_button = Button(
            screen, 621, 832, 319, 106, text='Vehicle',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.choose_vehicle_screen,
            textColour=textColour
        )
        self.tuning_button = Button(
            screen, 980, 832, 319, 106, text='Tuning',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.choose_tuning_screen,
            textColour=textColour
        )
        self.play_button = Button(
            screen, 1339, 832, 319, 106, text='Play',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.play,
            textColour=textColour
        )

        """Screens"""
        self.active_screen = None
        left_button = Button(
            screen, 392, 664, 100, 100, text='<',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.swipe_car,
            textColour=textColour
        )
        right_button = Button(
            screen, 1428, 664, 100, 100, text='>',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.swipe_car,
            textColour=textColour,
            userData="next"
        )
        left_button2 = Button(
            screen, 262, 664, 100, 100, text='<',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.swipe_level,
            textColour=textColour
        )
        right_button2 = Button(
            screen, 1558, 664, 100, 100, text='>',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.swipe_level,
            textColour=textColour,
            userData="next"
        )

        self.tuning_screen = [CategoryButton((262, 237), (318, 500), "Upgrade", lambda x: print("Hi")),
                              CategoryButton((621, 237), (318, 500), "Upgrade", lambda x: print("Hi")),
                              CategoryButton((980, 237), (318, 500), "Upgrade", lambda x: print("Hi")),
                              CategoryButton((1339, 237), (318, 500), "Upgrade", lambda x: print("Hi"))]

        self.level_screen = [left_button2, right_button2,
                             CategoryButton((413, 151), (1093, 613), "Countryside", self.choose_level, radius=0)]

        self.vehicle_screen = [left_button, right_button,
                               CategoryButton((557, 158), (806, 613), "Jeep",
                                              onClick=self.choose_car, radius=0)]
        self.active_screen = self.level_screen

        self.levels = self.get_levels()
        self.cars = self.get_cars()

        self.levels_names = list(self.levels.keys())
        self.car_names = list(self.cars.keys())

        self.player_data = self.load_player_data()

        self.chosen_level_index = 0
        self.choosen_car_index = 0

        self.shown_car_index = 0
        self.shown_level_index = 0
        self.update_category_buttons()

        self.running = False
        self.loaded_level = None
        self.start_time = int(round(time.time() * 1000))
        pygame.mixer.music.load('sounds/menu.mp3')
        pygame.mixer.music.play(-1, fade_ms=2000)

    def load_player_data(self):
        """Загрузка данных игрока"""
        with open("data/player_data.json") as f:
            data = json.load(f)
            return data

    @property
    def player_levels(self):
        """Уровни, которые есть у игрока"""
        return self.player_data["levels"]

    @property
    def player_cars(self):
        """Транспорт, который есть у игрока"""
        return self.player_data["cars"]

    @property
    def chosen_car_name(self):
        """Название выбранного автомобиля"""
        return self.car_names[self.choosen_car_index]

    @property
    def chosen_level_name(self):
        """Название выбранного уровня"""
        return self.levels_names[self.chosen_level_index]

    def swipe_car(self, source=None):
        """Переключение автомобиля в меню"""
        if source.userData == 'next':
            self.shown_car_index = min(len(self.car_names) - 1, self.shown_car_index + 1)
        else:
            self.shown_car_index = max(0, self.shown_car_index - 1)
        self.update_category_buttons()

    def swipe_level(self, source=None):
        """Переключение уровня в меню"""
        if source.userData == "next":
            self.shown_level_index = min(len(self.levels_names) - 1, self.shown_level_index + 1)
        else:
            self.shown_level_index = max(0, self.shown_level_index - 1)
        self.update_category_buttons()

    def get_upgraded_parameters(self):
        """Получение 'прокаченных' параметров у автомобиля"""
        upgrade_values = self.player_data["cars"][self.chosen_car_name]
        car_data = self.get_cars()[self.chosen_car_name]
        for parameter, level in upgrade_values.items():
            upgrade_data = car_data["upgrades"][parameter]
            one_part = (upgrade_data["max_value"] - car_data["parameters"][parameter]) / upgrade_data["levels"]
            upgrade_values[parameter] = level * one_part + car_data["parameters"][parameter]
        return upgrade_values

    def play(self, source=None):
        """Запуск уровня"""
        self.running = True
        modifications = self.get_upgraded_parameters()
        self.loaded_level = Level(level=self.chosen_level_name,
                                  vehicle=self.chosen_car_name,
                                  menu=self,
                                  vehicle_modifications=modifications)
        while self.running:
            self.loaded_level.update()
        self.start_time = int(round(time.time() * 1000))

    def update_player_data(self):
        """Загрузка данных игрока в переменную self.player_data"""
        self.player_data = self.load_player_data()

    def choose_vehicle_screen(self, source=None):
        """Выбор экрана выбора транспорта"""
        self.active_screen = self.vehicle_screen

    def choose_level_screen(self, source=None):
        """Выбор экрана выбора уровня"""
        self.active_screen = self.level_screen

    def choose_tuning_screen(self, source=None):
        """Выбор экрана тюнинга автомобиля"""
        self.load_upgrades(self.chosen_car_name)
        self.active_screen = self.tuning_screen

    def update(self, surface):
        """Обновление экрана главного меню"""
        events = pygame.event.get()
        surface.fill(self.BACKGROUND_COLOR)

        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()

        self.world_button.listen(events)
        self.world_button.draw()

        self.vehicle_button.listen(events)
        self.vehicle_button.draw()

        self.tuning_button.listen(events)
        self.tuning_button.draw()

        self.play_button.listen(events)
        self.play_button.draw()

        self.text = sf_pro_font_36.render('{0:,}'.format((self.player_data["money"])).replace(",", " ") + "$", True,
                                          (255, 255, 255))
        surface.blit(self.text, (1561, 84))

        alpha_value = max(0, 255 - ((int(round(time.time() * 1000)) - self.start_time)))

        for elem in self.active_screen:
            elem.listen(events)
            elem.draw()

        if alpha_value:
            pygame.gfxdraw.filled_polygon(surface,
                                          (
                                              (0, 0), (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT),
                                              (0, SCREEN_HEIGHT)),
                                          (0, 0, 0, alpha_value))
        pygame.display.flip()

    def get_cars(self):
        """Получение всех автомобилей в игре"""
        with open("data/cars_settings.json") as f:
            cars = json.load(f)
        return cars

    def get_levels(self):
        """Получение всех уровней в игре"""
        with open("data/levels.json") as f:
            levels = json.load(f)
        return levels

    def load_upgrades(self, car_name):
        """Подгрузка прокаченных параметров машины пользователя для обновления экрана тюнинга"""
        car_data = self.get_cars()[self.chosen_car_name]
        upgrades = self.load_player_data()["cars"][car_name]
        for category_button, upgrade_name in zip(self.tuning_screen, list(upgrades.keys())):
            upgrade_data = car_data["upgrades"][upgrade_name]
            max_level = upgrade_data["levels"]
            current_level = self.player_data["cars"][self.chosen_car_name][upgrade_name]
            if max_level != current_level:
                start_price = upgrade_data["start_price"]
                price_multiplier = upgrade_data["price_multiplier"]
                price = int(start_price * current_level * price_multiplier)
                price = '{0:,}'.format((price)).replace(",", " ")
            else:
                price = "Full"
            image = load_image(f"upgrades/{upgrade_name}.png")
            category_button.set_content(fontSizeBack=48,
                                        text=str(price), onClick=self.upgrade,
                                        userData=upgrade_name, image=image)

    def upgrade(self, source):
        """Прокачка автомобиля"""
        car = self.chosen_car_name
        upgrade_value = source.userData

        current_level = self.player_data["cars"][car][upgrade_value]
        car_data = self.get_cars()[car]

        upgrade_data = car_data["upgrades"][upgrade_value]
        max_level = upgrade_data["levels"]
        start_price = upgrade_data["start_price"]
        price_multiplier = upgrade_data["price_multiplier"]
        price = start_price * current_level * price_multiplier
        if current_level < max_level and self.player_data["money"] >= price:
            self.player_data["money"] = int(self.player_data["money"] - price)
            self.player_data["cars"][car][upgrade_value] += 1
        self.save_player_data()
        self.load_upgrades(self.chosen_car_name)

    def update_category_buttons(self):
        """Обновление всех значящих кнопок в меню"""
        if self.shown_level_index == 0:
            self.level_screen[0].hidden = True
        else:
            self.level_screen[0].hidden = False
        if self.shown_level_index == len(self.levels_names) - 1:
            self.level_screen[1].hidden = True
        else:
            self.level_screen[1].hidden = False

        if self.shown_car_index == 0:
            self.vehicle_screen[0].hidden = True
        else:
            self.vehicle_screen[0].hidden = False
        if self.shown_car_index == len(self.car_names) - 1:
            self.vehicle_screen[1].hidden = True
        else:
            self.vehicle_screen[1].hidden = False

        image = load_image(
            self.levels[self.levels_names[self.shown_level_index]]["preview"])

        level_name = self.levels_names[self.shown_level_index]
        if level_name in self.player_levels:
            self.level_screen[-1].onClick = self.choose_level
            self.level_screen[-1].set_content(level_name, onClick=self.choose_level, image=image)
        else:
            image.set_alpha(100)
            self.level_screen[-1].onClick = self.buy_level
            self.level_screen[-1].set_content(f"{level_name} - {self.levels[level_name]['price']}$",
                                              backText="LOCKED", image=image)

        image = load_image(
            self.cars[self.car_names[self.shown_car_index]]["preview"])
        car_name = self.car_names[self.shown_car_index]
        if car_name in self.player_cars:
            self.vehicle_screen[-1].onClick = self.choose_car
            self.vehicle_screen[-1].set_content(car_name, onClick=self.choose_car, image=image)
        else:
            image.set_alpha(100)
            self.vehicle_screen[-1].onClick = self.buy_car
            self.vehicle_screen[-1].set_content(f"{car_name} - {self.cars[car_name]['price']}$",
                                                backText="LOCKED", image=image)

    def choose_car(self, source=None):
        """Выбор автомобиля"""
        self.choosen_car_index = self.shown_car_index
        self.choose_tuning_screen()

    def choose_level(self, source=None):
        """Выбор уровня"""
        self.chosen_level_index = self.shown_level_index
        self.choose_vehicle_screen()

    def buy_car(self, source=None):
        """Покупка автомобиля"""
        car_name = self.car_names[self.shown_car_index]
        car_data = self.get_cars()[car_name]
        price = car_data["price"]
        if price <= self.player_data["money"]:
            self.player_data["money"] = int(self.player_data["money"] - price)
            self.player_data["cars"][car_name] = {k: 1 for k in list(car_data["upgrades"].keys())}
            self.save_player_data()
            self.update_category_buttons()

    def buy_level(self, source=None):
        """Покупка уровня"""
        level_name = self.levels_names[self.shown_level_index]
        level_data = self.get_levels()[level_name]
        price = level_data["price"]
        if price <= self.player_data["money"]:
            self.player_data["money"] = int(self.player_data["money"] - price)
            self.player_data["levels"][level_name] = {"record": 0, "next-stage": level_data["stage-step"]}
            self.save_player_data()
            self.update_category_buttons()

    def save_player_data(self):
        """Сохранение"""
        with open("data/player_data.json", mode="w") as f:
            json.dump(self.player_data, f)


class Wheel:
    def __init__(self, physical_world, parent, image, name='Wheel',
                 wheel_position=(1, 1),
                 wheel_density=1,
                 wheel_friction=1,
                 wheel_size=1,
                 sprite_group=None):
        """Класс колеса автомобиля"""
        image = load_image(image)
        x, y = parent.position
        self.wheel_body = physical_world.CreateDynamicBody(
            position=(x + wheel_position[0], y - wheel_position[1]))
        self.wheel_body.userData = name

        wheel_cirle = self.wheel_body.CreateCircleFixture(radius=wheel_size,
                                                          density=wheel_density,
                                                          friction=wheel_friction)
        torsoCarJointDef = b2WheelJointDef()
        torsoCarJointDef.Initialize(
            bodyA=parent,
            bodyB=self.wheel_body,
            anchor=self.wheel_body.position,
            axis=b2Vec2(0, 1.1),
        )
        self.wheel_joint_left = physical_world.CreateJoint(torsoCarJointDef)
        self.wheel_image = pygame.transform.scale(image,
                                                  (int(wheel_size * PPM) * 2, int(PPM * wheel_size) * 2))
        self.wheel_loc_center = self.wheel_image.get_width() // 2, self.wheel_image.get_height() // 2

        self.sprite = pygame.sprite.Sprite(sprite_group)
        self.sprite.image = self.wheel_image
        self.sprite.rect = self.sprite.image.get_rect()

    @property
    def angle(self):
        """Угол вращения колеса (Rad)"""
        return self.wheel_body.angle

    @property
    def angularVelocity(self):
        """Скорость вращения колеса"""
        return self.wheel_body.angularVelocity

    @property
    def position(self):
        """Позиция колеса (m)"""
        return self.wheel_body.position

    def update(self):
        """Обновление колеса"""
        wheel_pos = invert(self.position * PPM)[0]
        self.sprite.image, self.sprite.rect.topleft = rotate_image(self.wheel_image, wheel_pos,
                                                                   self.wheel_loc_center,
                                                                   self.angle * 180.0 / 3.14)

    def __sub__(self, other):
        """Уменьшение скорости вращения"""
        self.wheel_body.angularVelocity -= other

    def __add__(self, other):
        """Увеличение скорости вращения"""
        self.wheel_body.angularVelocity += other


class Terrain:
    CHUNK_SIZE = 10
    tile_position = b2Vec2(0, -30)
    n = 0

    def __init__(self, level):
        """Класс поверхности"""
        self.PHYSICAL_WORLD = level.PHYSICAL_WORLD
        self.terrains = list()
        self.enities_chunks = list()
        self.level = level
        self.last_world_coords = b2Vec2(0, 0)
        self.entities_sprite_group = pygame.sprite.Group()
        random.seed(level.RANDOM_SEED)

    def create_chunk(self):
        """Создание следующего чанка"""
        chunk = []
        entities_in_chunk = []
        for k in range(self.CHUNK_SIZE):
            last_tile, entity = self.create_chunk_tile(self.tile_position,
                                                       math.radians(random.randint(-self.level.MAX_ANGLE,
                                                                                   self.level.MAX_ANGLE)))
            chunk.append(last_tile)
            if entity is not None:
                entities_in_chunk.append(entity)
            last_fixture = last_tile.fixtures
            if last_fixture[0].shape.vertices[3] == b2Vec2(0, 0):
                self.last_world_coords = last_tile.GetWorldPoint(last_fixture[0].shape.vertices[0])
            else:
                self.last_world_coords = last_tile.GetWorldPoint(last_fixture[0].shape.vertices[3])
            self.tile_position = self.last_world_coords

        if len(self.terrains) > 1:
            chunk.append(self.create_border())

            # Удаляем предыдущий чанк
            for body in self.terrains[0]:
                self.PHYSICAL_WORLD.DestroyBody(body)
            self.terrains = self.terrains[1:]
            self.entities_sprite_group.remove(*self.enities_chunks[0])
            self.enities_chunks = self.enities_chunks[1:]

        self.enities_chunks.append(entities_in_chunk)
        self.terrains.append(chunk)
        return chunk, entities_in_chunk

    def create_border(self, chunk_index=1):
        """Создание левого края карты"""
        # Делаем левый ограничитель, чтобы юзер не выпал за край карты
        pos = self.terrains[chunk_index][0].position.x - 2, self.terrains[chunk_index][0].position.y + 40
        border = self.PHYSICAL_WORLD.CreateStaticBody(position=pos)
        border.userData = "border"
        box = border.CreatePolygonFixture(box=(2, 100))
        return border

    @property
    def first_chunk_pos(self):
        """Позиция первой клетки первого чанка в метрах"""
        return self.terrains[0][0].position

    @property
    def last_chunk_position(self):
        """Позиция последней клетки первого чанка в метрах"""
        return self.tile_position

    def create_chunk_tile(self, position, angle):
        """Создание клетки чанка"""
        self.n += 1
        groundPieceHeight, groundPieceWidth = 80, random.randint(10, 30)
        body_def = b2BodyDef()
        body_def.position = position
        body = self.PHYSICAL_WORLD.CreateBody(body_def)
        body.userData = 't'
        fix_def = b2FixtureDef()
        fix_def.shape = b2PolygonShape()
        fix_def.friction = 1

        coords = [b2Vec2(0, 0), b2Vec2(0, groundPieceHeight), b2Vec2(groundPieceWidth, groundPieceHeight),
                  b2Vec2(groundPieceWidth, 0)]

        newcoords = self.rotate_floor_tile(coords, angle)

        newcoords[2].x = newcoords[3].x
        newcoords[1].x = newcoords[0].x
        newcoords[2].y = newcoords[3].y + groundPieceHeight
        newcoords[1].y = newcoords[0].y + groundPieceHeight

        fix_def.shape = b2PolygonShape(vertices=newcoords)
        body.CreateFixture(fix_def)

        entity = None
        if self.level.has_entities and self.n % self.level.LEVEL_ENTITIES_FREQUENCY == 0:
            pos_x, pos_y = invert((position.x * PPM, (position.y + groundPieceHeight) * PPM))[0]
            entity = self.add_entity((pos_x, pos_y), angle=angle)

        return body, entity

    def rotate_floor_tile(self, coords, angle):
        """Вращаем прямоугольник клетки для разнообразия рельефа"""
        newcoords = []
        for k in range(len(coords)):
            nc = b2Vec2(0, 0)
            nc.x = math.cos(angle) * coords[k].x - math.sin(angle) * coords[k].y
            nc.y = math.sin(angle) * coords[k].x + math.cos(angle) * coords[k].y
            newcoords.append(nc)
        return newcoords

    def draw_entities(self, surface):
        """Отрисовка всех статичных объектов-спрайтов сцены"""
        """
        self.entities_sprite_group.draw(surface) тут не подойдёт,
         так как нам нужно менять позиции
        спрайтов относительно сдвига камеры
        """
        for sprite in self.entities_sprite_group:
            surface.blit(sprite.image, self.level.camera.apply(sprite))

    def add_entity(self, pos, angle=0):
        """Добавление статичного объекта-спрайта на сцену"""
        angle = math.degrees(angle)
        pos = list(pos)

        entity_name = random.choice(list(self.level.LEVEL_ENTITIES.keys()))
        entity_data = self.level.LEVEL_ENTITIES_DATA[entity_name]
        entity_image = self.level.LEVEL_ENTITIES[entity_name]

        sprite = Sprite(self.entities_sprite_group)
        sprite.image = entity_image
        sprite.rect = sprite.image.get_rect()

        align = entity_data["align"]
        pos[1] += entity_data["delta-y"]

        if align == "bottomleft":
            sprite.rect.bottomleft = pos
            sprite.image, sprite.rect.topleft = rotate_image(entity_image, sprite.rect.bottomleft,
                                                             entity_image.get_rect().bottomleft, angle)
        if align == "bottomright":
            sprite.rect.bottomright = pos
        if align == "midbottom":
            sprite.rect.midbottom = pos
            sprite.image, sprite.rect.topleft = rotate_image(entity_image, sprite.rect.midbottom,
                                                             entity_image.get_rect().midbottom, angle)
        return sprite


class Camera:
    delta_y = 0
    delta_x = 0
    offset = shake()

    def __init__(self, width, height):
        """Класс камеры для 'слежки' за объектами"""
        self.state = pygame.Rect(0, 0, width, height)
        self.restrictions = pygame.Rect(0, 0, 1000, 1000)

    def set_new_restrictions(self, startx=None, endx=None, starty=None, endy=None):
        """Изменение ограничений камеры"""
        if startx is not None:
            self.restrictions.x = startx
        if starty is not None:
            self.restrictions.y = starty
        if endx is not None:
            self.restrictions.w = endx
        if endy is not None:
            self.restrictions.h = endy

    def apply(self, target):
        """Изменённые координаты левого верхнего угла спрайта относительно камеры"""
        return target.rect.move(self.state.left + self.delta_x, self.state.top + self.delta_y)

    def apply_coords(self, coords):
        """Изменённые координаты относительно камеры"""
        x, y = coords
        return x + self.state.x + self.delta_x, y + self.state.top + self.delta_y

    def update_xy(self, coords):
        """Изменение цели камеры"""
        global delta_x, delta_y
        self.state = self.coords_func(coords)
        delta_x, delta_y = -self.state.x - self.delta_x, self.state.y + self.delta_y

    def coords_func(self, target_coords):
        """Ограничения камеры"""
        l, t, = target_coords
        _, _, w, h = self.state
        l, t = -l + SCREEN_WIDTH / 2, t - SCREEN_HEIGHT / 2 + 100
        l = min(-self.restrictions.x, l)
        return Rect(l, t, w, h)


class ListenerManager(b2ContactListener):
    def __init__(self, *listeners):
        """Прослушка коллизий"""
        b2ContactListener.__init__(self)
        self.listeners = listeners

    def BeginContact(self, contact):
        """Начало контакта"""
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        if fixture_a.body.userData is not None or fixture_b.body.userData is not None:
            for listener in self.listeners:
                listener.BeginContact(contact)

    def EndContact(self, contact):
        """Конец контакта"""
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        if fixture_a.body.userData is not None or fixture_b.body.userData is not None:
            for listener in self.listeners:
                listener.EndContact(contact)

    def PreSolve(self, contact, oldManifold):
        """пресолв коллизии"""
        pass

    def PostSolve(self, contact, impulse):
        """пост-солв коллизии"""
        pass


class Car:
    def __init__(self, vehicle_code="", level=None, position=(10, 70), modifications=None):
        """Класс самого автомобиля"""
        with open("data/cars_settings.json", "r") as read_file:
            car_data = json.load(read_file)
            if vehicle_code not in car_data:
                raise ValueError("Can't find car in json file")
            car_data = car_data[vehicle_code]
            parameters = car_data["parameters"]
            sprites = car_data["sprites"]

            # Константы для кастомизации автомобиля
            # Максимальная достигаемая скорость (Вперёд)
            self.MAX_CAR_SPEED = parameters["MAX_CAR_SPEED"]

            # Максимальная достигаемая скорость (Назад)
            self.MAX_CAR_REVERSE_SPEED = parameters["MAX_CAR_REVERSE_SPEED"]

            # Ускорение
            self.ACCELERATION = parameters["ACCELERATION"]

            # Эффективность тормозов
            self.BRAKES = parameters["BRAKES"]

            # Ширина Авто
            self.CAR_WIDTH = parameters["CAR_WIDTH"]

            # Высота Авто
            self.CAR_HEIGHT = parameters["CAR_HEIGHT"]

            # Сцепление
            self.CAR_FRICTION = parameters["CAR_FRICTION"]

            # Дельта для спрайта корпуса
            self.BODY_SPRITE_DELTA = tuple(parameters["BODY_SPRITE_DELTA"])

            # Размер для спрайта корпуса
            self.BODY_SPRITE_SCALE = tuple(parameters["BODY_SPRITE_SCALE"])

            # Масса автомобиля
            self.BODY_DENSITY = parameters["BODY_DENSITY"]

            # Запас топлива
            self.MAX_FUEL = parameters["MAX_FUEL"]

            # Все колёса автомобиля
            self.WHEELS_DATA = parameters["wheels"]

            self.ROTATION_SPEED = parameters["ROTATION_SPEED"]

            self.wheel_image = load_image(sprites["wheel"])
            self.car_body_image = load_image(sprites["body"])
            self.car_body_image = pygame.transform.scale(self.car_body_image, (
                int(self.BODY_SPRITE_SCALE[0] * PPM * 2), int(self.BODY_SPRITE_SCALE[1] * PPM * 2)))

        # Применение модификаций к автомобилю
        if modifications is not None:
            for key in modifications:
                if hasattr(self, key):
                    setattr(self, key, modifications[key])

        # Переменные
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self.sprite_group = pygame.sprite.Group()
        self.fuel = self.MAX_FUEL

        # Физическое положени автомобиля
        self.car_flips_n = 0
        self.takeoff_time = -1

        # Инициализация спрайта корпуса автомобиля
        self.BODY_SPRITE = pygame.sprite.Sprite(self.sprite_group)
        self.BODY_SPRITE.image = self.car_body_image
        self.BODY_SPRITE.rect = self.BODY_SPRITE.image.get_rect()

        # Рассчёты для корпуса и колёс
        x, y = position
        w, h = (self.CAR_WIDTH, self.CAR_HEIGHT)

        # Связь с уровнем
        self.PHYSICAL_WORLD = level.PHYSICAL_WORLD
        self.level = level

        # Инициализация физического тела корпуса
        self.main_body = self.PHYSICAL_WORLD.CreateDynamicBody(position=(x, y))
        self.main_body.userData = "car_body"
        main_body_fixture = self.main_body.CreatePolygonFixture(box=(w, h), density=self.BODY_DENSITY, friction=1)

        self.wheel_grounding = {}
        self.wheels = []
        self.flipped_frame_counter = 0

        # Создание всех колёс
        for wheel_name in self.WHEELS_DATA:
            wheel_data = self.WHEELS_DATA[wheel_name]
            wheel_density = wheel_data["WHEEL_DENSITY"]
            wheel_size = wheel_data["WHEEL_SIZE"]
            wheel_position = wheel_data["WHEEL_POSITION"]
            new_wheel = Wheel(self.PHYSICAL_WORLD, self.main_body, sprites["wheel"],
                              wheel_position=wheel_position,
                              wheel_density=wheel_density,
                              wheel_size=wheel_size,
                              wheel_friction=self.CAR_FRICTION,
                              sprite_group=self.sprite_group,
                              name=wheel_name)
            self.wheel_grounding[wheel_name] = False
            self.wheels.append(new_wheel)

    @property
    def is_grounded(self):
        """Автомобиль ноходится на земле"""
        return all(self.wheel_grounding.values())

    @property
    def speed(self):
        """Скорость автомобиля"""
        return round(abs(self.main_body.linearVelocity.x) + abs(self.main_body.linearVelocity.y), 2)

    @property
    def rpm(self):
        """Обороты в минуту"""
        rpm = 0
        for wheel in self.wheels:
            rpm += abs(wheel.angularVelocity)
        rpm /= len(self.wheels)
        return rpm

    @property
    def longitude(self):
        """Положение автомобиля по координате X"""
        return self.main_body.position.x

    @property
    def position(self):
        """Положение автомобиля"""
        return self.main_body.position

    def refuel(self):
        """Заправка автомобиля"""
        self.fuel = self.MAX_FUEL

    @property
    def can_drive(self):
        """Может ли автомобиль продолжать движение"""
        return self.fuel > 0 and not self.flipped_frame_counter > 100

    def tilt_left(self):
        """Наклон влево"""
        self.main_body.angularVelocity += self.ROTATION_SPEED / 10

    def tilt_right(self):
        """Наклон вправо"""
        self.main_body.angularVelocity -= self.ROTATION_SPEED / 10

    def move(self):
        """Нажатие на педаль газа"""
        for wheel in self.wheels:
            if wheel.wheel_body.angularVelocity > -self.MAX_CAR_SPEED:
                wheel.wheel_body.angularVelocity -= self.ACCELERATION

    def brake(self):
        """Торможение"""
        for wheel in self.wheels:
            if wheel.wheel_body.angularVelocity < self.MAX_CAR_SPEED:
                wheel.wheel_body.angularVelocity += self.ACCELERATION

    def release(self):
        """Применение силы трения"""
        idle_brake_speed = 0.2
        for wheel in self.wheels:
            try:
                if wheel.angularVelocity > 0:
                    wheel -= idle_brake_speed
                if wheel.angularVelocity < 0:
                    wheel += idle_brake_speed
            except AttributeError:
                continue

    def update(self, events):
        """Обновление автомобиля"""
        for event in events:
            if event.type == pygame.USEREVENT + 2:
                self.fuel = max(self.fuel - 1, 0)
        self.rect.x, self.rect.y = self.main_body.position * PPM
        dx, dy = self.BODY_SPRITE_DELTA
        car_body_image_center = self.car_body_image.get_width() // 2, self.car_body_image.get_height() // 2
        car_body_center = self.main_body.position[0] * PPM + dx, SCREEN_HEIGHT - self.main_body.position[1] * PPM - dy

        self.BODY_SPRITE.image, self.BODY_SPRITE.rect.topleft = rotate_image(self.car_body_image,
                                                                             car_body_center, car_body_image_center,
                                                                             self.main_body.angle * 180.0 / 3.14)
        for wheel in self.wheels:
            wheel.update()

        rotation_angle = math.degrees(self.main_body.angle)

        # Flip tracker
        if rotation_angle + 30 >= 360 * (self.car_flips_n + 1):
            self.car_flips_n += 1
            menu.loaded_level.display_message("Backflip! +1000", 5)
            self.level.backflips += 1
            self.level.level_money += 1000
        if rotation_angle - 30 <= 360 * (self.car_flips_n - 1):
            self.car_flips_n -= 1
            menu.loaded_level.display_message("Frontflip! +1000", 5)
            self.level.frontflips += 1
            self.level.level_money += 1000

        if not self.is_grounded and self.speed == 0:
            self.flipped_frame_counter += 1
        else:
            self.flipped_frame_counter = 0

    def BeginContact(self, contact):
        """Обработка начала коллизии"""

        wheels_names = set(self.wheel_grounding.keys())
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        data_a, data_b = body_a.userData, body_b.userData

        # Связано ли касание с нашим авто?
        if data_a not in wheels_names and data_b not in wheels_names:
            return
        if data_a in wheels_names:
            self.wheel_grounding[data_a] = True
        if data_b in wheels_names:
            self.wheel_grounding[data_b] = True
        if self.takeoff_time != -1 and time.time() - self.takeoff_time > 2 and self.is_grounded:
            # Длинный прыжок
            self.level.shake_camera()
            menu.loaded_level.display_message(f"Long jump! {round(time.time() - self.takeoff_time, 1)}", 5)
            self.level.airtimes += 1
            self.level.level_money += int(round(time.time() - self.takeoff_time, 1) * 1000)

    def EndContact(self, contact):
        """Обработка конца коллизии"""

        wheels_names = ("left_wheel", "right_wheel")
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        data_a, data_b = body_a.userData, body_b.userData

        # Связано ли касание с нашим авто?
        if data_a not in wheels_names and data_b not in wheels_names:
            return

        if data_a in wheels_names:
            self.wheel_grounding[data_a] = False
        if data_b in wheels_names:
            self.wheel_grounding[data_b] = False

        if not self.is_grounded:
            self.takeoff_time = time.time()

    def distance_to(self, point, count_y=True):
        """Расчёт расстояния между автотобилем и точкой"""
        x, y = point
        sx, sy = self.main_body.position
        return abs(sx - x) + ((sy - y) if count_y else 0)


class Level:
    def __init__(self, level=None, vehicle=None, menu=None, vehicle_modifications=None):
        """Класс уровня"""
        global LINE_COLOR, colors, GROUND_TEXTURE

        self.modifications = vehicle_modifications
        # Подгружаем параметры уровня из json
        self.VEHICLE_CODE = vehicle
        self.LEVEL_CODE = level
        self.menu = menu
        self.level_money = 0
        self.exit_level_timer = None
        with open("data/levels.json", "r") as read_file:
            LEVELS_DATA = json.load(read_file)
            if level not in LEVELS_DATA:
                raise ValueError("Can't find level in json file")
            level_parameters = LEVELS_DATA[level]
            GROUND_TEXTURE = load_image(level_parameters["ground-texture"])
            self.PHYSICAL_WORLD = world(gravity=(0, level_parameters["gravity"]))
            self.MAX_ANGLE = level_parameters["max-angle"]
            self.LINE_COLOR = level_parameters["line-color"]
            self.BACKGROUND_TEXTURE = load_image(level_parameters["bg-texture"])
            self.level_record = self.menu.player_levels[level]["record"]
            self.next_target = self.menu.player_levels[level]["next-stage"]
            self.stage_step = self.menu.levels[level]["stage-step"]

            self.LEVEL_ENTITIES = []

            colors["l"] = self.LINE_COLOR

            if "level-entities" in level_parameters:
                self.LEVEL_ENTITIES_DATA = level_parameters["level-entities"]
                self.LEVEL_ENTITIES = {x: load_image(self.LEVEL_ENTITIES_DATA[x]["path"]) for x in
                                       self.LEVEL_ENTITIES_DATA}
            self.LEVEL_ENTITIES_FREQUENCY = level_parameters["level-entities-frequency"]

            self.RANDOM_SEED = level_parameters["seed"]

        # Загружаем авто
        self.vehicle = Car(self.VEHICLE_CODE, self, modifications=self.modifications)

        # Создаём камеру
        self.camera = Camera(1000000, 1000)

        # Слушатель контактов для отслеживания коллизий
        self.PHYSICAL_WORLD.contactListener = ListenerManager(self.vehicle)

        # Ивент для перемотки
        self.start_time = int(round(time.time() * 1000))

        # Создаём землю
        self.terrain = Terrain(self)
        self.terrain.create_chunk()
        self.terrain.create_border(0)

        self.next_checkpoint = self.stage_step
        self.is_paused = False

        inactive = (100, 100, 100)
        pressed = (160, 160, 160)
        textColour = (255, 255, 255)
        self.pause_menu_screen = [Button(
            screen, 1233, 611, 580, 120, text="Resume",
            inactiveColour=inactive,
            pressedColour=pressed,
            radius=20,
            textColour=textColour,
            onClick=lambda x: self.pause(),
            fontSize=48,
        ),
            Button(
                screen, 1233, 767, 580, 120, text="Restart",
                inactiveColour=inactive,
                pressedColour=pressed,
                radius=20,
                textColour=textColour,
                onClick=lambda x: self.reset(),
                fontSize=48,
            ),

            Button(
                screen, 1233, 923, 580, 120, text="Menu",
                inactiveColour=inactive,
                pressedColour=pressed,
                radius=20,
                textColour=textColour,
                onClick=lambda x: self.exit(),
                fontSize=48,
            )
        ]
        self.last_message_display_time = 99999999999999999999999999999
        self.message_text = ""
        self.frontflips, self.backflips = 0, 0
        self.airtimes = 0
        self.display_message(f"Reach {self.next_target}m for additional points!", 3)
        self.last_image = None

        pygame.mixer.music.load('sounds/game.mp3')
        pygame.mixer.music.play(-1, fade_ms=2000)

    @property
    def has_entities(self):
        """На уровне есть объекты-спрайты"""
        return self.LEVEL_ENTITIES != []

    def end_level(self):
        """Завершение уровня, gameover экран"""
        if self.exit_level_timer is None:
            self.exit_level_timer = pygame.time.get_ticks()
        if self.vehicle.fuel == 0:
            self.display_message("Out of Fuel!", 100)
        else:
            self.display_message("Flipped over!", 100)
        if (pygame.time.get_ticks() - self.exit_level_timer) / 1000 > 5:
            self.gameover_screen_running = True
            gameover_menu = GameOverScreen(self)
            while self.gameover_screen_running:
                gameover_menu.update(screen)
            self.exit()

    def pause(self):
        """Пауза"""
        self.is_paused = not self.is_paused

    def save(self):
        """Сохранение денег и рекордов"""
        with open("data/player_data.json") as f:
            data = json.load(f)
            data["money"] = int(data["money"] + self.level_money)
            data["levels"][self.LEVEL_CODE]["record"] = self.level_record
            data["levels"][self.LEVEL_CODE]["next-stage"] = self.next_target
        with open("data/player_data.json", mode="w") as f:
            json.dump(data, f)
        self.menu.update_player_data()

    def reset(self):
        """Перезапуск уровня"""
        for body in self.PHYSICAL_WORLD.bodies:
            self.PHYSICAL_WORLD.DestroyBody(body)
        pygame.mixer.music.load('sounds/game.mp3')
        pygame.mixer.music.play(-1, fade_ms=2000)
        self.terrain = Terrain(self)
        self.terrain.create_chunk()
        self.terrain.create_border(0)
        self.next_checkpoint = self.stage_step
        self.camera.set_new_restrictions(startx=0)
        self.is_paused = False
        self.start_time = int(round(time.time() * 1000))
        self.vehicle = Car(self.VEHICLE_CODE, self, modifications=self.modifications)

    def exit(self):
        """Выход в главное меню"""
        pygame.mixer.music.load('sounds/menu.mp3')
        pygame.mixer.music.play(-1, fade_ms=2000)
        self.save()
        self.menu.running = False

    def update(self):
        """Обновление уровня"""
        global camera

        try:
            pygame.gfxdraw.textured_polygon(screen, ((0, 0), (SCREEN_WIDTH, 0),
                                                     (SCREEN_WIDTH, SCREEN_HEIGHT),
                                                     (0, SCREEN_HEIGHT)), self.BACKGROUND_TEXTURE, 0,
                                            0)
        except:
            pass
        camera = self.camera
        keys = pygame.key.get_pressed()
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.pause()

        camera.delta_x, camera.delta_y = next(camera.offset)
        if self.next_checkpoint - self.vehicle.longitude < 80:
            checkpoint_coords = camera.apply_coords((self.next_checkpoint * PPM, 0))[0], 0
            cx, cy = checkpoint_coords
            try:
                pygame.gfxdraw.textured_polygon(screen, ((cx, 0), (cx + 30, 0),
                                                         (cx + 30, SCREEN_HEIGHT),
                                                         (cx, SCREEN_HEIGHT)), checkpoint_tile, -int(delta_x) % 30,
                                                -int(delta_y) % 40)
            except:
                pass
        if self.vehicle.longitude >= self.next_checkpoint:
            self.next_checkpoint += self.stage_step
            self.display_message(f"Checkpoint reached! Car refueled!", 3)
            self.vehicle.refuel()
        if self.vehicle.longitude >= self.next_target:
            self.next_target += self.stage_step
            self.display_message(f"Next target - {self.next_target}m! +1000", 3)
            self.level_money += 1000
            self.vehicle.refuel()
        if self.vehicle.longitude > self.level_record:
            self.level_record = int(self.vehicle.longitude)

        if self.vehicle.can_drive:
            if keys[pygame.K_r]:
                self.reset()
            if keys[pygame.K_d]:
                self.vehicle.move()
                self.vehicle.tilt_left()
            elif keys[pygame.K_a]:
                self.vehicle.brake()
                self.vehicle.tilt_right()
            else:
                self.vehicle.release()
        else:
            self.vehicle.release()
            self.end_level()

        self.terrain.draw_entities(screen)

        for body in self.PHYSICAL_WORLD.bodies:
            for fixture in body.fixtures:
                fixture.shape.update(body, fixture)

        if self.vehicle.distance_to(self.terrain.last_chunk_position, count_y=False) <= 80:
            self.terrain.create_chunk()
            camera.set_new_restrictions(startx=self.terrain.first_chunk_pos.x * PPM)

        self.vehicle.update(events)

        for sprite in self.vehicle.sprite_group:
            screen.blit(sprite.image, self.camera.apply(sprite))

        if not self.vehicle.can_drive:
            rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            sub = screen.subsurface(rect)
            screenshot = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            screenshot.blit(sub, (0, 0))
            self.last_image = screenshot

        alpha_value = max(0, 255 - ((int(round(time.time() * 1000)) - self.start_time) // 2))
        if alpha_value:
            pygame.gfxdraw.filled_polygon(screen,
                                          (
                                              (0, 0), (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT),
                                              (0, SCREEN_HEIGHT)),
                                          (0, 0, 0, alpha_value))

        if not self.is_paused:
            self.PHYSICAL_WORLD.Step(TIME_STEP, 10, 10)
            self.draw_ui()
            self.camera.update_xy(self.vehicle.position * PPM)
        else:
            pos = self.vehicle.position * PPM
            pos = (pos[0] + 400, pos[1])
            for elem in self.pause_menu_screen:
                elem.listen(events)
                elem.draw()
            self.camera.update_xy(pos)

        pygame.display.flip()
        clock.tick(TARGET_FPS)

    def get_fuel_bar_color(self, percent):
        """Получение цвета полоски по процентам"""
        try:
            return fuel_bar_colors.get_at((int(fuel_bar_colors.get_width() / 100 * percent) - 1, 0))
        except IndexError:
            return (255, 0, 0)

    def draw_ui(self):
        """Отрисовка элементов интерфейса"""

        filled_fuel = pygame.Surface((fuel_rect.get_width(), fuel_rect.get_height()))
        filled_fuel.fill(self.get_fuel_bar_color(self.vehicle.fuel / self.vehicle.MAX_FUEL * 100))
        fuel_fill = pygame.transform.scale(filled_fuel,
                                           (int(self.vehicle.fuel / self.vehicle.MAX_FUEL * filled_fuel.get_width()),
                                            filled_fuel.get_height()))
        screen.blit(fuel_fill, (130, 120))
        screen.blit(fuel_rect, (130, 120))
        screen.blit(double_arrow, (7, 0))
        screen.blit(fuel_icon, (18, 104))
        screen.blit(coin_icon, (18, 197))

        # Distance
        distance_text = f"{int(self.vehicle.longitude)}m/{self.next_target}m (BEST: {self.level_record}m)"
        distance = sf_pro_font_72.render(distance_text, True,
                                         (255, 255, 255))
        screen.blit(distance, (120, 40))

        # Coins
        coins_text = int(self.level_money + self.menu.player_data["money"])
        coins_text = '{0:,}'.format((coins_text)).replace(",", " ")
        coins = sf_pro_font_72.render(coins_text, True,
                                      (255, 255, 255))
        screen.blit(coins, (120, 220))

        # Speedometer
        screen.blit(speedometer_bg, (704, 800))
        screen.blit(taxometer_bg, (960, 800))

        MAX_SPEED = 90
        MAX_RPM = 90
        degrees1 = -int(min(self.vehicle.speed, MAX_SPEED) / MAX_SPEED * 266 - 133)
        degrees2 = -int(min(self.vehicle.rpm, MAX_RPM) / MAX_RPM * 266 - 133)
        poiner_origin_point = 16, 104
        global_pointer_pos1 = 832, 931
        global_pointer_pos2 = 1087, 931

        """
        LENGTH = 90
        ORIGIN = (832, 927)
        POINT = (ORIGIN[0] - LENGTH, 900)
        new_point = rotate_around_point(POINT, degrees, ORIGIN)
        pygame.draw.line(screen, (145, 37, 38), ORIGIN, new_point, 5)
        """

        pointer1, new_origin1 = rotate_image(speedometer_pointer, global_pointer_pos1, poiner_origin_point, degrees1)
        pointer2, new_origin2 = rotate_image(speedometer_pointer, global_pointer_pos2, poiner_origin_point, degrees2)
        screen.blit(pointer1, new_origin1)
        screen.blit(pointer2, new_origin2)

        if self.next_checkpoint - self.vehicle.longitude < 100:
            to_fuel_text = f"{int(self.next_checkpoint - self.vehicle.longitude)}m to"
            to_fuel = sf_pro_font_72.render(to_fuel_text, True,
                                            (255, 255, 255))
            screen.blit(to_fuel, (1606, 50))
            screen.blit(fuel_icon, (1780, 36))
        if self.last_message_display_time >= time.time():
            message = sf_pro_font_72.render(self.message_text, True, (255, 255, 255))
            screen.blit(message, (696, 208))

    def display_message(self, text, secs):
        """Отображение сообщения на экране"""
        self.last_message_display_time = time.time() + secs
        self.message_text = text

    def shake_camera(self):
        """Встряхнуть камеру"""
        self.camera.offset = shake()


class GameOverScreen:
    """Шрифты:"""
    sf_pro_font_100 = pygame.font.Font(
        r"data/SFProDisplay-Regular.ttf", 100)
    sf_pro_font_72 = pygame.font.Font(
        r"data/SFProDisplay-Regular.ttf", 72)
    sf_pro_font_64 = pygame.font.Font(
        r"data/SFProDisplay-Regular.ttf", 64)

    def __init__(self, level):
        """Класс экрана Game Over"""

        # Связь с уровнем
        self.level = level
        self.last_image = level.last_image

        # Рендерим все элементы
        self.reason = "OUT OF FUEL!" if level.vehicle.fuel == 0 else "FLIPPED OVER!"
        self.reason = self.sf_pro_font_100.render(self.reason, True, (255, 255, 255))
        self.record = f"Record: {self.level.level_record}m"
        self.record = self.sf_pro_font_72.render(self.record, True, (255, 255, 255))
        self.coins = f"+{self.level.level_money} Coins"
        self.coins = self.sf_pro_font_72.render(self.coins, True, (255, 255, 255))
        self.flips = f"x{self.level.frontflips} Frontflip x{self.level.backflips} Backflip"
        self.flips = self.sf_pro_font_72.render(self.flips, True, (255, 255, 255))
        self.airtimes = f"x{self.level.airtimes} Air time"
        self.airtimes = self.sf_pro_font_72.render(self.airtimes, True, (255, 255, 255))

        self.click = f"CLICK TO CONTINUE"
        self.click = self.sf_pro_font_72.render(self.click, True, (255, 255, 255))
        self.click_opacity = 255
        self.click_opacity_increasing = False

        # Делаем снимок машинки
        car_pos = self.level.camera.apply_coords(self.level.vehicle.BODY_SPRITE.rect.center)
        car_pos = list(car_pos)
        car_pos[0] = max(car_pos[0] - 250, 0)
        car_pos[1] = max(car_pos[1] - 250, 0)
        rect = pygame.Rect(*car_pos, int(700 / 1.3), int(580 / 1.3))
        sub = self.last_image.subsurface(rect)
        ui_frame = pygame.Surface((811, 811), pygame.SRCALPHA, 32)
        ui_frame.blit(pygame.transform.scale(sub, (700, 580)), (38, 36))

        # Накладываем полароидную рамочку
        ui_frame.blit(frame, (0, 0))

        # Пишем на фотке
        stunts = f"{self.level.airtimes}xAIRTIME, {self.level.frontflips + self.level.backflips}xFLIP"
        stunts = self.sf_pro_font_64.render(stunts, True, (86, 86, 86))
        ui_frame.blit(stunts, (117, 646))
        meters = f"{int(self.level.vehicle.longitude)}m"
        meters = self.sf_pro_font_100.render(meters, True, (255, 255, 255))
        ui_frame.blit(meters, (352, 52))
        level_name = f"IN {self.level.LEVEL_CODE.upper()}"
        level_name = self.sf_pro_font_72.render(level_name, True, (255, 255, 255))
        ui_frame.blit(level_name, (352, 147))

        self.ui_frame = ui_frame

        # Вращаем снимок
        self.car_image = Sprite()
        self.car_image.image = ui_frame
        self.car_image.rect = self.car_image.image.get_rect()
        self.car_image.image, self.car_image.rect.topleft = rotate_image(ui_frame, (100, 200), (0, 0), 7)
        self.start_time = time.time()

    def transition(self, image, percent, position=(100, 100)):
        """Применение перехода к элементам интерфейса"""
        angle = min(0, -(90 / 100 * (100 - percent)))
        opacity = min(255 / 100 * percent, 255)
        rotated_image, new_origin = rotate_image(image, position,
                                                 (image.get_width() // 2, image.get_height() // 2),
                                                 angle)
        rotated_image.set_alpha(opacity)
        return rotated_image, new_origin

    def update(self, surface):
        """Обновление - отрисовка"""
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.level.gameover_screen_running = False

        # Задний фон - картинка + тинт
        surface.blit(self.last_image, (0, 0))

        pygame.gfxdraw.filled_polygon(surface, ((0, 0), (SCREEN_WIDTH, 0),
                                                (SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)),
                                      (0, 0, 0, 100))
        surface.blit(self.car_image.image, self.car_image.rect.topleft)

        time_delta = int((time.time() - self.start_time) * 1000) * 2
        if time_delta in (1000, 2000, 3000, 4000, 5000):
            tab_sound.play()
        reason, reason_point = self.transition(self.reason, time_delta / 10, (1405, 260))
        surface.blit(reason, reason_point)

        record, record_point = self.transition(self.record, max(0, time_delta - 1000) / 10, (1405, 423))
        surface.blit(record, record_point)

        coins, coins_point = self.transition(self.coins, max(0, time_delta - 2000) / 10, (1405, 510))
        surface.blit(coins, coins_point)

        flips, flips_point = self.transition(self.flips, max(0, time_delta - 3000) / 10, (1405, 597))
        surface.blit(flips, flips_point)

        airtimes, airtimes_point = self.transition(self.airtimes, max(0, time_delta - 4000) / 10, (1405, 684))
        surface.blit(airtimes, airtimes_point)

        if self.click_opacity_increasing:
            self.click_opacity = min(255, self.click_opacity + 10)
            if self.click_opacity == 255:
                self.click_opacity_increasing = False
        else:
            self.click_opacity = max(30, self.click_opacity - 10)
            if self.click_opacity == 30:
                self.click_opacity_increasing = True
        self.click = f"CLICK TO CONTINUE"
        self.click = self.sf_pro_font_72.render(self.click, True,
                                                (255, 255, 255))
        self.click.set_alpha(self.click_opacity)
        surface.blit(self.click, (1071, 795))
        pygame.display.update()
        clock.tick(100)


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Hill climb racing")
clock = pygame.time.Clock()
pygame.time.set_timer(pygame.USEREVENT + 2, 200)

polygonShape.update = my_draw_polygon
circleShape.update = my_draw_circle
colors = {"t": (29, 29, 29, 255),
          "car_body": (255, 255, 255, 255),
          "l": (255, 255, 255, 255),
          2: (255, 0, 255),
          }

# UI
fuel_bar_colors = load_image("UI/fuel_bar_colors.png")
GROUND_TEXTURE = load_image("ground/terrain_ground.png")

sf_pro_font_36 = pygame.font.Font(
    r"data/SFProDisplay-Regular.ttf", 48)
sf_pro_font_72 = pygame.font.Font(
    r"data/SFProDisplay-Regular.ttf", 72)

speedometer_bg = load_image("UI/speedometer_bg.png")
taxometer_bg = load_image("UI/taxometer_bg.png")
speedometer_pointer = load_image("UI/speedometer_pointer.png")
coin_icon = load_image("UI/coin_icon.png")
fuel_icon = load_image("UI/fuel_icon.png")
filled_fuel = load_image("UI/filled_fuel.png")
fuel_rect = load_image("UI/fuel_rect.png")
double_arrow = load_image("UI/double_arrow.png")
frame = load_image("UI/frame.png")
checkpoint_tile = load_image("checkpoint.png")
checkpoint_tile.set_alpha(100)
button_sound = pygame.mixer.Sound("sounds/button.mp3")
tab_sound = pygame.mixer.Sound("sounds/tab.mp3")
menu = MainMenu()
while True:
    menu.update(screen)
