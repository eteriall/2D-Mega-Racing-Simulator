# 2D Mega-Racing Simulator 
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/eteriall/2D-Mega-Racing-Simulator)
![Lines of code](https://img.shields.io/tokei/lines/github/eteriall/2D-Mega-Racing-Simulator) 
![PygameV](https://img.shields.io/badge/pygame-2.0.0-brightgreen)
![Box2dV](https://img.shields.io/badge/Box2d-2.3.10-brightgreen)


Гоночный 2D симулятор, написанный на Python 3.8 с использованием библиотеки pygame и Box2D для симуляции физики.
-  [Последний релиз](https://github.com/eteriall/2D-Mega-Racing-Simulator/releases/download/v1.1/Setup_2D_Mega-Racing_Simulator.exe)
-  [ Скриншоты из игры](https://github.com/eteriall/2D-Mega-Racing-Simulator#фотографии-из-игры)
-  [ Документация моддинга транспорта](https://github.com/eteriall/2D-Mega-Racing-Simulator#создание-новых-автомобилей)
-  [Документация моддинга уровней](https://github.com/eteriall/2D-Mega-Racing-Simulator#создание-новых-уровней)



## Установка
Хотите поиграть? [Cкачайте последнюю версию игры](https://github.com/eteriall/2D-Mega-Racing-Simulator/releases/download/v1.1/Setup_2D_Mega-Racing_Simulator.exe)!

Если вы хотите модифицировать __исходный код__ или просто посмотреть -
как и что работает:

1. Склонируйте этот репозиторий на ваше устройство:

    `git clone https://github.com/eteriall/2D-Mega-Racing-Simulator.git`
    
2. Установите все необходимые модули:

    `pip install -r requirements.txt`

3. Запустите скрипт _game.py_:

    `python3 game.py`

3. __Наслаждайтесь!__

## Модификация автомобилей, уровней и игровых объектов
Любой начинающий программист может написать расширение для нашей игры!
Пользователи могут добавлять транспорт и уровни. Сейчас расскажу, как.
Данная опция доступна в обеих версиях - и с исходным кодом, и с
скомпилированным исполняемым файлом.

### Создание новых автомобилей
1. Откройте файл `/data/cars_settings.json`
2. В этом файле хранятся все параметры автомобилей в игре. Вы также
   можете модифицировать параметры уже существующих автомобилей.
3. Чтобы добавить совершенно новый автомобиль - вставьте в файл
   следующую структуру:
   ```
   "My-car": {
    "price": 0,
    "preview": "previews/my-car-preview.png",
    "parameters": {
      "MAX_FUEL": 100,
      "MAX_CAR_SPEED": 15,
      "MAX_CAR_REVERSE_SPEED": 10,
      "ACCELERATION": 1,
      "ROTATION_SPEED": 1,
      "BRAKES": 3,
      "CAR_WIDTH": 4,
      "CAR_HEIGHT": 1,
      "CAR_FRICTION": 30,
      "BODY_DENSITY": 1,
      "BODY_SPRITE_DELTA": [
        -3,
        0
      ],
      "BODY_SPRITE_SCALE": [
        5,
        2.5
      ],
      "wheels": {
        "left_wheel": {
          "WHEEL_DENSITY": 5,
          "WHEEL_SIZE": 1,
          "WHEEL_POSITION": [
            -3,
            2.4
          ]
        },
        "right_wheel": {
          "WHEEL_DENSITY": 5,
          "WHEEL_SIZE": 1,
          "WHEEL_POSITION": [
            3,
            2.4
          ]
        }
      }
    },
    "sprites": {
      "body": "cars/my-car-body.png",
      "wheel": "wheels/my-car-tire.png"
    },
    "upgrades": {
      "MAX_CAR_SPEED": {
        "start_price": 10000,
        "price_multiplier": 1.5,
        "max_value": 30,
        "levels": 5
      },
      "ACCELERATION": {
        "start_price": 10000,
        "price_multiplier": 1.5,
        "max_value": 5,
        "levels": 3
      },
      "MAX_FUEL": {
        "start_price": 10000,
        "price_multiplier": 1.5,
        "max_value": 300,
        "levels": 5
      },
      "CAR_FRICTION": {
        "start_price": 10000,
        "price_multiplier": 1.5,
        "max_value": 100,
        "levels": 5
      }
    }
   }
    ```

   В этой структуре находится вся информация об автомобиле - его
   максимальная скорость, положение каждого колеса, стоимость автомобиля
   и т.д.

   Рассмотрим каждый из параметров:
   - `my-car` - Вместо этого параметра - укажите название нового
     транспорта
   - `price` - Стоимость автомобиля
   - `preview` - Путь к превью автомобиля. Картинка должна быть размером
     806x613px
   - `parameters` - Все параметры автомобиля
     - `MAX_FUEL` - Количество топлива в автомобиле
     - `MAX_CAR_SPEED` - Максимальная скорость автомобиля
     - `MAX_CAR_REVERSE_SPEED` - Максимальная скорость автомобиля при
       движении назад
     - `ACCELERATION` - Ускорение автомобиля
     - `BRAKES` - Сила торможения
     - `ROTATION_SPEED` - Управляемость автомобиля в воздухе
     - `CAR_WIDTH` - Ширина тела автомобиля
     - `CAR_HEIGHT` - Высота тела автомобиля
     - `CAR_FRICTION` - Уровень сцепления автомобиля с дорогой
     - `BODY_DENSITY` - Плотность тела автомобиля
     - `BODY_SPRITE_DELTA` - Сдвиг спрайта тела автомобиля (в игровых
       метрах)
     - `BODY_SPRITE_SCALE` - Размер спрайта тела автомобиля (в игровых
       метрах)
     - `wheels` - Все колёса нашего транспорта
       - `left_wheel` или же `right_wheel` - системные названия для
         колёс. Вместо этого параметра - укажите название нового колеса
         для нового транспорта. Названия колёс не должны повторяться.
       - `WHEEL_DENSITY` - Плотность колеса
       - `WHEEL_SIZE` - Диаметр колеса в метрах
       - `WHEEL_POSITION` - Положение колеса относительно центра тела
         автомобиля
   - `sprites` - Спрайты для автомобиля
     - `body` - Путь к спрайту тела автомобиля
     - `wheel` - Путь к спрайту колеса автомобиля
   - `upgrades` - Прокачиваемые параметры автомобиля. Их __ОБЯЗАТЕЛЬНО__
     должно быть 4.
     -  `MAX_CAR_SPEED` - Вместо этого параметра укажите прокачиваемый
        параметр. Всего существует 7 прокачиваемых параметров:
        -  `MAX_FUEL`
        -  `MAX_CAR_SPEED`
        -  `ACCELERATION`
        -  `BRAKES`
        -  `CAR_FRICTION`
        -  `BODY_DENSITY`
        -  `ROTATION_SPEED`
     - `start_price` - Начальная цена обновления.
     - `price_multiplier` - Множитель итоговой стоимости. Стоимость
       апгрейда высчиывается по формуле номер_текущего_уровня *
       стартовая_цена * множитель_итоговой_стоимости.
     - `max_value` - Максимальное значение прокачиваеиого параметра.
       Минимальное значение указывается в параметрах конфигурации самого
       автомобиля.
     - `levels` - Количество уровней

    Изменяя все вышеперечисленные параметры в прикреплённой структуре вы
    можете создавать новые автомобили для игры! Если автомобиль не
    отображается в списке автомобилей в игре или игра не запускается
    после внесённых изменений - проверьте, нет ли ошибок в структуре
    файла, все ли параметры указаны верно. Если же ничего не помогает -
    [скачайте файл](https://github.com/eteriall/HillClimbRacing/blob/master/source/data/cars_settings.json)
    заново.

### Создание новых уровней
1. Откройте файл `/data/levels.json`
2. В этом файле хранятся все параметры всех уровней в игре. Вы также
   можете модифицировать параметры уже существующих уровней.
3. Чтобы добавить совершенно новый уровень - вставьте в файл следующую
   структуру:
   ```
   "my-level-name" : {
    "line-color": [255, 255, 255],
    "ground-texture": "ground/terrain_ground.png",
    "bg-texture": "bg/countryside_bg.png",
    "seed": "hills",
    "stage-step": 300,
    "preview": "previews/my-level-preview.png",
    "level-entities-frequency": 5,
    "gravity": -35,
    "max_angle": 30,
    "price": 0,
    "level-entities": {
        "my-entity": {
            "path": "your_object.png",
            "align": "midbottom",
            "delta_y": 10
      }  
    }
   ```
   Замените `my-level-name` на название вашего уровня.
   - `line-color` - Цвет линии 'перелома'
   - `ground-texture` - Путь к изображению с текстурой земли
   - `bg-texture` - Путь к изображению с текстурой заднего фона
   - `seed` - Сид генерации мира
   - `stage-step` - Кол-во метров между чекпойнтами
   - `preview` - Путь к изображению с превью уровня. Картинка должна быть
   размером 1093x609px.
   - `level-entities-frequency` - Частота появления объектов заднего
   плана. Чем меньше число - тем чаще появляется объект. Минимальное
   значение - 1.
   - `gravity` - Сила притяжения к земле.
   - `max_angle` - Максимальный угол 'перелома' рельефа.
   - `price` - Стоимость уровня
   - `level-entities` - Объекты заднего плана. (Необязательный параметр)
   - - Замените `my-entity` на тэг для вашего объекта.
     - `path` - Путь к изображению с вашим объектом
     - `align` - Точка, за которую спрайт объекта будет крепиться на
       земле. Значения параметра:
       - `midbottom` - Центр, нижняя сторона.
       - `bottomleft` - Левый нижний угол.
       - `bottomright` - Правый нижний угол.
       - `delta_y` - Сдвиг вашего объекта по оси Y.

   Изменяя все вышеперечисленные параметры в прикреплённой структуре вы
   можете создавать новые уровни для игры! Если уровень не отображается
   в игре после внесённых изменений - проверьте, нет ли ошибок в
   структуре файла, все ли параметры указаны верно. Если же ничего не
   помогает -
   [скачайте файл](https://github.com/eteriall/HillClimbRacing/blob/master/source/data/levels.json)
   заново.

## Фотографии из игры
![screenshot0](https://github.com/eteriall/HillClimbRacing/blob/master/source/screenshots/screenshot0.png)

![screenshot](https://github.com/eteriall/2D-Mega-Racing-Simulator/blob/master/source/screenshots/screenshot.png)

![screenshot2](https://github.com/eteriall/HillClimbRacing/blob/master/source/screenshots/screenshot2.png)
