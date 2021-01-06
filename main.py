import json
import math
import os
import random
import sys
import time
import pygame
from pygame import gfxdraw

import collision
import pygame
from Box2D import Box2D, b2WheelJointDef, b2Vec2, b2FixtureDef, b2BodyDef, b2PolygonShape, b2ContactListener
from Box2D.b2 import world, polygonShape, circleShape, staticBody, dynamicBody
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame_widgets import Button as BrokenButton

pygame.init()
pygame.mixer.init()
PPM = 20
TARGET_FPS = 120
TIME_STEP = 1.0 / TARGET_FPS
SCREEN_WIDTH, SCREEN_HEIGHT = 1880, 1000
DEBUG = False


class Button(BrokenButton):
    def __init__(self, win, x, y, width, height, **kwargs):
        super(Button, self).__init__(win, x, y, width, height, **kwargs)

    def listen(self, events):
        """Мне не понравилось, как отрабатывает функция прослушки событий поэтому я её переписал."""
        if not self.hidden:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.contains(*event.pos):
                        self.onClick(*self.onClickParams)
            x, y = pygame.mouse.get_pos()
            if self.contains(x, y) and pygame.mouse.get_pressed(3)[0]:
                self.colour = self.pressedColour
            elif self.contains(x, y):
                self.colour = self.hoverColour
            else:
                self.colour = self.inactiveColour


class CategoryButton:
    bg_color = (77, 77, 77)
    inactive = (100, 100, 100)
    pressed = (160, 160, 160)
    textColour = (255, 255, 255)

    def __init__(self, xy, wh, text, onClick, image=None):
        self.size = (xy, wh)
        x, y = xy
        w, h = wh
        self.onClick = onClick
        self.back = Button(
            screen, x, y, w, h, text='',
            inactiveColour=self.bg_color,
            pressedColour=self.bg_color,
            radius=20,
            image=image,
            imageVAlign="bottom"
        )

        margin = 20
        x, y = x + margin, y + h - 80 - margin
        w, h = w - 2 * margin, 80
        self.front = Button(
            screen, x, y, w, h, text=text,
            inactiveColour=self.inactive,
            pressedColour=self.pressed,
            radius=20,
            textColour=self.textColour,
            onClick=onClick,
            fontSize=48,
        )

    def set_content(self, text, image=None):
        xy, wh = self.size
        x, y = xy
        w, h = wh
        margin = 20
        x, y = x + margin, y + h - 80 - margin
        w, h = w - 2 * margin, 80
        self.front = Button(
            screen, x, y, w, h, text=text,
            inactiveColour=self.inactive,
            pressedColour=self.pressed,
            radius=20,
            textColour=self.textColour,
            onClick=self.onClick,
            fontSize=48,
        )
        self.back = Button(
            screen, x, y, w, h, text='',
            inactiveColour=self.bg_color,
            pressedColour=self.bg_color,
            radius=20,
            image=image
        )

    def draw(self):
        self.back.draw()
        self.front.draw()

    def listen(self, events):
        self.front.listen(events)


class MainMenu:
    def __init__(self):
        self.font = pygame.font.SysFont('calibri', 36)
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
            onClick=self.choose_vehicle,
            textColour=textColour
        )
        self.tuning_button = Button(
            screen, 980, 832, 319, 106, text='Tuning',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.customize_vehicle,
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
            onClick=self.previous_car,
            textColour=textColour
        )
        right_button = Button(
            screen, 1428, 664, 100, 100, text='>',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=self.next_car,
            textColour=textColour
        )
        self.vehicle_screen = [left_button, right_button,
                               CategoryButton((557, 158), (806, 613), "Quadrocycle",
                                              lambda: self.set_active_screen("tuning"))]

        self.tuning_screen = [CategoryButton((262, 237), (318, 500), "Upgrade", lambda: print("Hi")),
                              CategoryButton((621, 237), (318, 500), "Upgrade", lambda: print("Hi")),
                              CategoryButton((980, 237), (318, 500), "Upgrade", lambda: print("Hi")),
                              CategoryButton((1339, 237), (318, 500), "Upgrade", lambda: print("Hi"))]

        left_button = Button(
            screen, 262, 664, 100, 100, text='<',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=lambda: self.previous_level(),
            textColour=textColour
        )
        right_button = Button(
            screen, 1558, 664, 100, 100, text='>',
            fontSize=48, margin=20,
            inactiveColour=inactive,
            pressedColour=pressed, radius=20,
            onClick=lambda: self.next_level(),
            textColour=textColour
        )
        self.level_screen = [left_button, right_button,
                             CategoryButton((413, 151), (1093, 613), "Hills", lambda: self.set_active_screen("car"))]
        self.active_screen = self.level_screen

        self.levels = self.get_levels()
        self.cars = self.get_cars()

        self.levels_names = list(self.levels.keys())
        self.car_names = list(self.cars.keys())

        self.player_data = self.load_player_data()

        self.chosen_level_index = 0
        self.choosen_car_index = 0

        self.shown_car_index = 1
        self.shown_level_index = 3
        self.update_category_buttons()

    def load_player_data(self):
        with open("player_data.json") as f:
            data = json.load(f)
            return data

    def set_active_screen(self, screen_name):
        self.active_screen = {"car": self.vehicle_screen,
                              "level": self.level_screen,
                              "tuning": self.tuning_screen}[screen_name]

    def next_car(self):
        self.shown_car_index = min(len(self.car_names) - 1, self.shown_car_index + 1)
        self.update_category_buttons()

    def previous_car(self):
        self.shown_car_index = max(0, self.shown_car_index - 1)
        self.update_category_buttons()

    @property
    def player_levels(self):
        return self.player_data["levels"]

    @property
    def player_cars(self):
        return self.player_data["cars"]

    @property
    def player_cars_names(self):
        return list(self.player_data["cars"].keys())

    @property
    def player_levels_names(self):
        return list(self.player_data["levels"].keys())

    def next_level(self):
        self.shown_level_index = min(len(self.levels_names) - 1, self.shown_level_index + 1)
        self.update_category_buttons()

    def previous_level(self):
        self.shown_level_index = max(0, self.shown_level_index - 1)
        self.update_category_buttons()

    def play(self):
        self.running = True
        self.loaded_level = Level(level=self.levels_names[self.shown_level_index],
                                  vehicle=self.car_names[self.shown_car_index],
                                  menu=self)
        while self.running:
            self.loaded_level.update()

    def update_player_data(self):
        with open("player_data.json") as f:
            self.player_data = json.load(f)

    def choose_vehicle(self):
        self.active_screen = self.vehicle_screen

    def choose_level_screen(self):
        self.active_screen = self.level_screen

    def customize_vehicle(self):
        self.active_screen = self.tuning_screen

    def update(self, surface):
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

        self.text = self.font.render(str(self.player_data["money"]), True, (255, 255, 255))
        surface.blit(self.text, (1561, 84))

        for elem in self.active_screen:
            elem.listen(events)
            elem.draw()
        pygame.display.flip()

    def get_cars(self):
        with open("cars_settings.json") as f:
            cars = json.load(f)
        return cars

    def get_levels(self):
        with open("levels.json") as f:
            levels = json.load(f)
        return levels

    def update_category_buttons(self):

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
        if level_name in self.player_levels_names:
            self.level_screen[-1].onClick = self.choose_level
            self.level_screen[-1].set_content(level_name)
        else:
            self.level_screen[-1].onClick = self.buy_level
            self.level_screen[-1].set_content(f"{level_name} - {self.levels[level_name]['price']}")

        car_name = self.car_names[self.shown_car_index]
        if car_name in self.player_cars:
            self.vehicle_screen[-1].onClick = self.choose_car
            self.vehicle_screen[-1].set_content(car_name)
        else:
            self.vehicle_screen[-1].onClick = self.buy_car
            self.vehicle_screen[-1].set_content(f"{car_name} - {self.cars[car_name]['price']}")

    def buy_car(self):
        print(self.car_names[self.shown_car_index])

    def choose_car(self):
        self.choosen_car_index = self.shown_car_index

    def choose_level(self):
        self.chosen_level_index = self.shown_level_index

    def buy_level(self):
        print(self.levels_names[self.shown_level_index])


def checkCollision(sprite1, sprite2):
    return pygame.sprite.collide_rect(sprite1, sprite2)


def invert(*args):
    return list(map(lambda x: (x[0], SCREEN_HEIGHT - x[1]), args))


def rotate_image(image, pos, originPos, angle):
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


def load_image(name, size=None):
    fullname = os.path.join(r'C:\Users\d1520\Desktop\LyceumPygameProject\HillClimbRacing/sprites', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def my_draw_polygon(poly, body, fixture):
    if not DEBUG and body.userData in ("left_wheel", "right_wheel", "car_body", "border"):
        return
    vertices = [(body.transform * v) * PPM for v in poly.vertices]
    vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
    vertices = [camera.apply_coords(x) for x in vertices]

    try:
        """pygame.draw.polygon(screen, colors[body.userData], vertices, 1)"""
        gfxdraw.filled_polygon(screen, vertices, colors[body.userData])
        if body.userData == "t":
            xy1, xy2 = vertices[1:3]
            x1, y1, x2, y2 = list(map(int, xy1 + xy2))
            pygame.gfxdraw.aapolygon(screen, ((x1, y1), (x2, y2), (x2, y2)), colors["l"])
            pygame.draw.line(screen, colors["l"], (x1, y1), (x2, y2), 10)
    except KeyError:
        gfxdraw.filled_polygon(screen, vertices, (255, 0, 255))


def my_draw_circle(circle, body, fixture):
    if not DEBUG and body.userData in ("left_wheel", "right_wheel", "left", "right"):
        return
    position = body.transform * circle.pos * PPM
    position = (position[0], SCREEN_HEIGHT - position[1])
    position = list(map(int, camera.apply_coords(position)))

    try:
        gfxdraw.aacircle(screen, *position, int(circle.radius * PPM), colors[body.userData])
        gfxdraw.filled_circle(screen, *position, int(circle.radius * PPM), colors[body.userData])
    except KeyError:
        try:
            gfxdraw.aacircle(screen, *position, int(circle.radius * PPM), (255, 0, 255))
        except OverflowError:
            pygame.draw.circle(screen, (255, 0, 255), position, int(circle.radius * PPM), 2)


def rotate_around_point(xy, degrees, origin=(0, 0)):
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


class Wheel:
    def __init__(self, physical_world, parent, image, name='Wheel',
                 wheel_position=(1, 1),
                 wheel_density=1,
                 wheel_friction=1,
                 wheel_size=1,
                 sprite_group=None):
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
        return self.wheel_body.angle

    @property
    def angularVelocity(self):
        return self.wheel_body.angularVelocity

    @property
    def position(self):
        return self.wheel_body.position

    def update(self):
        wheel_pos = invert(self.position * PPM)[0]
        self.sprite.image, self.sprite.rect.topleft = rotate_image(self.wheel_image, wheel_pos,
                                                                   self.wheel_loc_center,
                                                                   self.angle * 180.0 / 3.14)

    def __sub__(self, other):
        self.wheel_body.angularVelocity -= other

    def __add__(self, other):
        self.wheel_body.angularVelocity += other


class Terrain:
    CHUNK_SIZE = 10
    tile_position = b2Vec2(0, -30)
    n = 0

    def __init__(self, level):
        self.PHYSICAL_WORLD = level.PHYSICAL_WORLD
        self.terrains = list()
        self.enities_chunks = list()
        self.level = level
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
        # Создание клетки чанка
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
        """Вращаем прямоугольничек клетки для разнообразия рельефа"""
        newcoords = []
        for k in range(len(coords)):
            nc = b2Vec2(0, 0)
            nc.x = math.cos(angle) * (coords[k].x) - math.sin(angle) * (coords[k].y)
            nc.y = math.sin(angle) * (coords[k].x) + math.cos(angle) * (coords[k].y)
            newcoords.append(nc)
        return newcoords

    def check_collision(self, obj2):
        for obj1 in self.terrains:
            try:
                if collision.collide(obj1, obj2, response=None):
                    return True
            except TypeError as e:
                print(obj1, obj2, e)
        return False

    def draw_entities(self, surface):
        for sprite in self.entities_sprite_group:
            surface.blit(sprite.image, self.level.camera.apply(sprite))

    def add_entity(self, pos, angle=0):
        angle = math.degrees(angle)
        pos = list(pos)

        entity_name = random.choice(list(self.level.LEVEL_ENTITIES.keys()))
        entity_data = self.level.LEVEL_ENTITIES_DATA[entity_name]
        entity_image = self.level.LEVEL_ENTITIES[entity_name]

        sprite = Sprite(self.entities_sprite_group)
        sprite.image = entity_image
        sprite.rect = sprite.image.get_rect()

        align = entity_data["align"]
        pos[1] += entity_data["delta_y"]

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
    delta_y = -500

    def __init__(self, width, height):
        self.state = pygame.Rect(0, 0, width, height)
        self.restrictions = pygame.Rect(0, 0, 1000, 1000)

    def set_new_restrictions(self, startx=None, endx=None, starty=None, endy=None):
        if startx is not None:
            self.restrictions.x = startx
        if starty is not None:
            self.restrictions.y = starty
        if endx is not None:
            self.restrictions.w = endx
        if endy is not None:
            self.restrictions.h = endy

    def apply(self, target):
        return target.rect.move(self.state.left, self.state.top)

    def apply_coords(self, coords):
        x, y = coords
        return x + self.state.x, y + self.state.top

    def update_xy(self, coords):
        self.state = self.coords_func(coords)

    def coords_func(self, target_coords):
        l, t, = target_coords
        _, _, w, h = self.state
        l, t = -l + SCREEN_WIDTH / 2, t - SCREEN_HEIGHT / 2 + 100
        l = min(-self.restrictions.x, l)  # Не движемся дальше левой границы

        """l = max(-(self.state.width - SCREEN_WIDTH), l)  # Не движемся дальше правой границы"""
        return Rect(l, t, w, h)


class ListenerManager(b2ContactListener):
    def __init__(self, *listeners):
        b2ContactListener.__init__(self)
        self.listeners = listeners

    def BeginContact(self, contact):
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        if body_a.userData is not None or body_b.userData is not None:
            ud_a, ud_b = body_a.userData, body_b.userData
            for listener in self.listeners:
                listener.BeginContact(contact)

    def EndContact(self, contact):
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        if body_a.userData is not None or body_b.userData is not None:
            ud_a, ud_b = body_a.userData, body_b.userData
            for listener in self.listeners:
                listener.EndContact(contact)

    def PreSolve(self, contact, oldManifold):
        pass

    def PostSolve(self, contact, impulse):
        pass


class Car:
    def __init__(self, vehicle_code="", level=None, position=(10, 70), ):
        with open("cars_settings.json", "r") as read_file:
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

            # Кол-во фреймов, на которые мы можем откатиться
            self.MAX_REVERSE_TIME_STEPS_AMOUNT = parameters["MAX_REVERSE_TIME_STEPS_AMOUNT"]

            self.MAX_FUEL = parameters["MAX_FUEL"]

            # Все колёса автомобиля
            self.WHEELS_DATA = parameters["wheels"]

            self.ROTATION_SPEED = parameters["ROTATION_SPEED"]

            self.wheel_image = load_image(sprites["wheel"])
            self.car_body_image = load_image(sprites["body"])
            self.car_body_image = pygame.transform.scale(self.car_body_image, (
                int(self.BODY_SPRITE_SCALE[0] * PPM * 2), int(self.BODY_SPRITE_SCALE[1] * PPM * 2)))

        # Переменные
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self.sprite_group = pygame.sprite.Group()
        self.fuel = self.MAX_FUEL

        # Перемотка времени
        self.last_positions = []
        self.reversing_time = False

        # Физическое положени автомобиля
        self.car_flips_n = 0
        self.is_grounded = False
        self.takeoff_time = -1
        self.left_wheel_is_grounded = False
        self.right_wheel_is_grounded = False

        # Инициализация спрайта корпуса автомобиля
        self.BODY_SPRITE = pygame.sprite.Sprite(self.sprite_group)
        self.BODY_SPRITE.image = self.car_body_image
        self.BODY_SPRITE.rect = self.BODY_SPRITE.image.get_rect()

        # Рассчёты для корпуса и колёс
        x, y = position
        w, h = (self.CAR_WIDTH, self.CAR_HEIGHT)

        self.PHYSICAL_WORLD = level.PHYSICAL_WORLD
        self.LEVEL = level
        # Инициализация физического тела корпуса
        self.main_body = self.PHYSICAL_WORLD.CreateDynamicBody(position=(x, y))
        self.main_body.userData = "car_body"
        main_body = self.main_body.CreatePolygonFixture(box=(w, h), density=self.BODY_DENSITY, friction=1)

        """"
            "WHEEL_DENSITY": 5,
            "WHEEL_SIZE": 1,
            "WHEEL_POSITION": [1.6, 2.4]
        """

        self.WHEELS = []
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
            self.WHEELS.append(new_wheel)

    @property
    def speed(self):
        return abs(self.main_body.linearVelocity.x) + abs(self.main_body.linearVelocity.y)

    @property
    def longitude(self):
        return self.main_body.position.x

    def refuel(self):
        self.fuel = self.MAX_FUEL

    @property
    def can_drive(self):
        return self.fuel > 0

    def tilt_left(self):
        self.main_body.angularVelocity += self.ROTATION_SPEED / 10

    def tilt_right(self):
        self.main_body.angularVelocity -= self.ROTATION_SPEED / 10

    def move(self):
        for wheel in self.WHEELS:
            if wheel.wheel_body.angularVelocity > -self.MAX_CAR_SPEED:
                wheel.wheel_body.angularVelocity -= self.ACCELERATION

    def brake(self):
        for wheel in self.WHEELS:
            if wheel.wheel_body.angularVelocity < self.MAX_CAR_SPEED:
                wheel.wheel_body.angularVelocity += self.ACCELERATION

    def release(self):
        idle_brake_speed = 0.1
        for wheel in self.WHEELS:
            """if wheel.angularVelocity > 0:
                wheel -= idle_brake_speed
            if wheel.angularVelocity < 0:
                wheel += idle_brake_speed"""

    def update(self, events):
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
        for wheel in self.WHEELS:
            wheel.update()

        rotation_angle = math.degrees(self.main_body.angle)

        # Flip tracker
        if rotation_angle + 30 >= 360 * (self.car_flips_n + 1):
            self.car_flips_n += 1
            menu.loaded_level.display_message("Backflip! +1000", 5)
            self.LEVEL.level_money += 1000
        if rotation_angle - 30 <= 360 * (self.car_flips_n - 1):
            self.car_flips_n -= 1
            menu.loaded_level.display_message("Frontflip! +1000", 5)
            self.LEVEL.level_money += 1000

        # Time reverse
        if self.reversing_time:
            self.reverse_step()
        if len(self.last_positions) == 0 and self.reversing_time:
            self.reversing_time = False
        if len(self.last_positions) > self.MAX_REVERSE_TIME_STEPS_AMOUNT:
            self.last_positions = self.last_positions[1:]

        """ # Last steps update
        if not False and pygame.time.get_ticks() % 1000000 == 0 and False:
            vec_body = self.main_body.position
            new_vec_body = b2Vec2(float(vec_body.x), float(vec_body.y))

            vec_left_wheel = self.left_wheel.position
            new_vec_left_wheel = b2Vec2(float(vec_left_wheel.x), float(vec_left_wheel.y))

            vec_right_wheel = self.right_wheel.position
            new_vec_right_wheel = b2Vec2(float(vec_right_wheel.x), float(vec_right_wheel.y))

            self.last_positions += [
                ((new_vec_body, float(self.main_body.angle)),
                 new_vec_left_wheel,
                 new_vec_right_wheel
                 )]"""

    def reverse_step(self):
        pass
        """if len(self.last_positions):
            pos = self.last_positions[-1]
            body_pos, body_rot = (pos[0][0].x, pos[0][0].y), pos[0][1]
            left_wheel, right_wheel = pos[1], pos[2]
            self.main_body.position = b2Vec2(*body_pos)
            self.main_body.angle = body_rot
            self.left_wheel.position = left_wheel
            self.right_wheel.position = right_wheel
            self.last_positions = self.last_positions[:-1]"""

    def reverse_full(self):
        self.reversing_time = True

    def BeginContact(self, contact):
        """Обработка начала коллизии"""

        varible_names = ("left_wheel", "right_wheel")
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        data_a, data_b = body_a.userData, body_b.userData

        # Связано ли касание с нашим авто?
        if data_a not in varible_names and data_b not in varible_names:
            return
        if self.takeoff_time != -1 and time.time() - self.takeoff_time > 2:
            # Длинный прыжок
            menu.loaded_level.display_message(f"Long jump! {round(time.time() - self.takeoff_time, 1)}", 5)
            self.LEVEL.level_money += round(time.time() - self.takeoff_time, 1) * 1000

        if "left_wheel" in (data_a, data_b):
            self.left_wheel_is_grounded = True
            self.takeoff_time = -1
        if "right_wheel" in (data_a, data_b):
            self.right_wheel_is_grounded = True
            self.takeoff_time = -1
        if "car_body" in (data_a, data_b):
            self.is_grounded = True
            self.takeoff_time = -1

    def EndContact(self, contact):
        """Обработка конца коллизии"""
        varible_fixtures_names = ("left_wheel", "right_wheel")
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        body_a, body_b = fixture_a.body, fixture_b.body
        data_a, data_b = body_a.userData, body_b.userData

        # Связано ли касание с нашим авто?
        if data_a not in varible_fixtures_names and data_b not in varible_fixtures_names:
            return

        if "left_wheel" in (data_a, data_b):
            self.left_wheel_is_grounded = False
        if "right_wheel" in (data_a, data_b):
            self.right_wheel_is_grounded = False

        if not self.left_wheel_is_grounded and not self.right_wheel_is_grounded:
            self.takeoff_time = time.time()
            self.is_grounded = False

    def distance_to(self, point, count_y=True):
        """Расчёт расстояния между автотобилем и точкой"""
        x, y = point
        sx, sy = self.main_body.position
        return abs(sx - x) + ((sy - y) if count_y else 0)


class Level:
    def __init__(self, level=None, vehicle=None, menu=None):
        global LINE_COLOR, colors

        # Подгружаем параметры уровня из json
        self.VEHICLE_CODE = vehicle
        self.LEVEL_CODE = vehicle
        self.menu = menu
        self.level_money = 0
        self.exit_level_timer = None

        with open("levels.json", "r") as read_file:
            LEVELS_DATA = json.load(read_file)
            if level not in LEVELS_DATA:
                raise ValueError("Can't find level in json file")
            level_parameters = LEVELS_DATA[level]
            self.PHYSICAL_WORLD = world(gravity=(0, level_parameters["gravity"]))
            self.MAX_ANGLE = level_parameters["max_angle"]
            self.BACKGROUND_COLOR = level_parameters["background"]
            self.LINE_COLOR = level_parameters["line-color"]
            colors["l"] = self.LINE_COLOR
            self.GROUND_COLOR = level_parameters["ground-color"]
            colors["t"] = self.GROUND_COLOR
            self.LEVEL_ENTITIES = []
            if "level_entities" in level_parameters:
                self.LEVEL_ENTITIES_DATA = level_parameters["level_entities"]
                self.LEVEL_ENTITIES = {x: load_image(self.LEVEL_ENTITIES_DATA[x]["path"]) for x in
                                       self.LEVEL_ENTITIES_DATA}
            self.LEVEL_ENTITIES_FREQUENCY = level_parameters["level_entities_frequency"]

            self.RANDOM_SEED = level_parameters["seed"]

        # Загружаем авто
        self.VEHICLE = Car(self.VEHICLE_CODE, self)

        # Создаём камеру
        self.camera = Camera(1000000, 1000)

        # Слушатель контактов для отслеживания коллизий
        self.PHYSICAL_WORLD.contactListener = ListenerManager(self.VEHICLE)

        # Ивент для перемотки
        pygame.time.set_timer(pygame.USEREVENT + 1, 10)

        # Создаём землю
        self.terrain = Terrain(self)
        self.terrain.create_chunk()
        self.terrain.create_border(0)

        self.IS_RUNNING = True
        self.IS_PAUSED = False

        self.last_message_display_time = 99999999999999999999999999999
        self.message_text = ""

    @property
    def has_entities(self):
        return self.LEVEL_ENTITIES != []

    def exit_level(self):
        if self.exit_level_timer is None:
            self.exit_level_timer = pygame.time.get_ticks()
        self.display_message("Fuel ended!", 100)
        if (pygame.time.get_ticks() - self.exit_level_timer) / 1000 > 5:
            self.save()
            menu.running = False

    def save(self):
        with open("player_data.json") as f:
            data = json.load(f)
            data["money"] += self.level_money
            data["money"] = int(data["money"])
        with open("player_data.json", mode="w") as f:
            json.dump(data, f)
        self.menu.update_player_data()

    def reset(self):
        for body in self.PHYSICAL_WORLD.bodies:
            self.PHYSICAL_WORLD.DestroyBody(body)

        self.terrain = Terrain(self)
        self.terrain.create_chunk()
        self.terrain.create_border(0)

        self.camera.set_new_restrictions(startx=0)
        self.VEHICLE = Car(self.VEHICLE_CODE, self)

    def update(self):
        global camera

        camera = self.camera
        screen.fill(self.BACKGROUND_COLOR)
        self.terrain.draw_entities(screen)

        btns = pygame.mouse.get_pressed(3)
        keys = pygame.key.get_pressed()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.save()
                self.menu.running = False
            if event.type == pygame.USEREVENT + 1 and self.VEHICLE.reversing_time:
                self.VEHICLE.reverse_step()
        if not self.IS_PAUSED:
            self.PHYSICAL_WORLD.Step(TIME_STEP, 10, 10)

        if self.VEHICLE.can_drive:
            if keys[pygame.K_r]:
                self.reset()
            if keys[pygame.K_d]:
                self.VEHICLE.move()
                self.VEHICLE.tilt_left()
            elif keys[pygame.K_a]:
                self.VEHICLE.brake()
                self.VEHICLE.tilt_right()
            else:
                self.VEHICLE.release()
        else:
            self.VEHICLE.release()
            self.exit_level()

        for body in self.PHYSICAL_WORLD.bodies:
            for fixture in body.fixtures:
                fixture.shape.update(body, fixture)

        if self.VEHICLE.distance_to(self.terrain.last_chunk_position, count_y=False) <= 80:
            self.terrain.create_chunk()
            camera.set_new_restrictions(startx=self.terrain.first_chunk_pos.x * PPM)

        self.VEHICLE.update(events)
        self.camera.update_xy(self.VEHICLE.main_body.position * PPM)

        for sprite in self.VEHICLE.sprite_group:
            screen.blit(sprite.image, self.camera.apply(sprite))

        self.draw_ui()
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    def get_fuel_bar_color(self, percent):
        try:
            return fuel_bar_colors.get_at((int(fuel_bar_colors.get_width() / 100 * percent) - 1, 0))
        except IndexError:
            return (255, 0, 0)

    def draw_ui(self):
        """fps_counter = sf_pro_font.render(str(int(clock.get_fps())), True,
                                         (255, 255, 255))

        screen.blit(fps_counter, (10, 50))"""

        filled_fuel = pygame.Surface((fuel_rect.get_width(), fuel_rect.get_height()))
        filled_fuel.fill(self.get_fuel_bar_color(self.VEHICLE.fuel / self.VEHICLE.MAX_FUEL * 100))
        fuel_fill = pygame.transform.scale(filled_fuel,
                                           (int(self.VEHICLE.fuel / self.VEHICLE.MAX_FUEL * filled_fuel.get_width()),
                                            filled_fuel.get_height()))
        screen.blit(fuel_fill, (130, 120))
        screen.blit(fuel_rect, (130, 120))
        screen.blit(double_arrow, (7, 0))
        screen.blit(fuel_icon, (18, 104))
        screen.blit(coin_icon, (18, 197))

        # Distance
        distance_text = f"{int(self.VEHICLE.longitude)}m/1830m (BEST: 1804m)"
        distance = sf_pro_font_72.render(distance_text, True,
                                         (255, 255, 255))
        screen.blit(distance, (120, 40))

        # Coins
        coins_text = str(int(self.level_money + self.menu.player_data["money"]))
        coins = sf_pro_font_72.render(coins_text, True,
                                      (255, 255, 255))
        screen.blit(coins, (120, 220))

        """# Speedometer
        screen.blit(speedometer_bg, (35, 770))
        speed = sf_pro_font_36.render(str(abs(round(self.VEHICLE.speed, 2))), True,
                                      (255, 255, 255))
        screen.blit(speed, (139, 985))
        MAX_SPEED = 90
        degrees = -int(min(self.VEHICLE.speed, MAX_SPEED) / MAX_SPEED * 260 - 40)
        LENGTH = 120
        ORIGIN = (166, 900)
        POINT = (ORIGIN[0] - LENGTH, 900)
        new_point = rotate_around_point(POINT, degrees, ORIGIN)
        pygame.draw.line(screen, (255, 255, 255), ORIGIN, new_point, 3)"""

        if self.last_message_display_time >= time.time():
            message = sf_pro_font_72.render(self.message_text, True, (255, 255, 255))
            screen.blit(message, (696, 208))

    def display_message(self, text, secs):
        self.last_message_display_time = time.time() + secs
        self.message_text = text


polygonShape.update = my_draw_polygon
circleShape.update = my_draw_circle
colors = {"t": (29, 29, 29, 255),
          "car_body": (255, 255, 255, 255),
          "l": (255, 255, 255, 255),
          2: (255, 0, 255),
          }

# UI
fuel_bar_colors = load_image("UI/fuel_bar_colors.png")
sf_pro_font_36 = pygame.font.Font(None, 36)
sf_pro_font_72 = pygame.font.Font(None, 72)
speedometer_bg = load_image("UI/speedometer.png")
coin_icon = load_image("UI/coin_icon.png")
fuel_icon = load_image("UI/fuel_icon.png")
filled_fuel = load_image("UI/filled_fuel.png")
fuel_rect = load_image("UI/fuel_rect.png")
double_arrow = load_image("UI/double_arrow.png")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Hill climb racing")
clock = pygame.time.Clock()
pygame.time.set_timer(pygame.USEREVENT + 2, 200)

menu = MainMenu()
while True:
    menu.update(screen)
