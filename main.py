import pygame
import time
import sys
import sqlite3

# Инициализация Pygame
pygame.init()

# Константы
win_width = 800
win_height = 700


# Функция для отображения видео в качестве фона
def play_video_background(frames):
    current_frame = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Отображение текущего кадра видео
        frame = frames[current_frame]
        frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        window.blit(frame_surface, (0, 0))

        # Обновление индекса кадра
        current_frame = (current_frame + 1) % len(frames)

        pygame.display.update()
        clock.tick(FPS)


# Основной цикл игры
clock = pygame.time.Clock()

# Запуск анимации на главном экране
FPS = 60
color = (255, 193, 37)
# Создание окна
window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption('Симулятор фермы')
background = pygame.transform.scale(pygame.image.load('background.jpg'), (win_width, win_height))
font2 = pygame.font.Font(None, 36)
pygame.mixer.music.load('X1.mp3')
pygame.mixer.music.play(-1)
# Игровые переменные
score = 0
coins = 0
exchange_rate = 0.5  # Коэффициент обмена звезд на монеты
exchange_x = 0
exchange_y = 0
exchange_zone_rect = pygame.Rect(exchange_x, exchange_y, 250, 280)
purchase_message = ""  # Переменная для сообщения о покупке
message_time = 0  # Время, когда сообщение было показано
message_duration = 3  # Длительность отображения сообщения в секундах
current_background_index = 0  # Инд
price1 = 100
price2 = 300
upgrade_price = 20  # Начальная цена прокачки
upgrade_multiplier = 2

controls = {
    'up': pygame.K_w,
    'down': pygame.K_s,
    'left': pygame.K_a,
    'right': pygame.K_d,
    'inventory': pygame.K_r,
    'harvest': pygame.K_f,
    'exchange': pygame.K_e,
    'exit': pygame.K_ESCAPE
}


# Функция для инициализации базы данных
def init_db():
    conn = sqlite3.connect('game_data.db')  # Создаем или открываем базу данных
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_data (
            id INTEGER PRIMARY KEY,
            score INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('SELECT * FROM game_data')
    if cursor.fetchone() is None:  # Если таблица пустая, добавляем начальные значения
        cursor.execute('INSERT INTO game_data (score, coins) VALUES (0, 0)')
    conn.commit()
    conn.close()


# Функция для сохранения данных в базе данных
def save_game_data():
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE game_data SET score = ?, coins = ?', (score, coins))
    conn.commit()
    conn.close()


# Функция для загрузки данных из базы данных
def load_game_data():
    global score, coins
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT score, coins FROM game_data')
    data = cursor.fetchone()
    if data:
        score, coins = data
    conn.close()


background_sprites = {
    0: [],  # Для первого фона
    1: [],  # Для второго фона
    2: []  # Для третьего фона
}
# Инициализируем базу данных
init_db()
# Загружаем данные при старте игры
load_game_data()


class MusicButton:
    def __init__(self, x, y):
        self.image_on = pygame.image.load('musical-note.png')  # Изображение для включенной музыки
        self.image_off = pygame.image.load('music.png')  # Изображение для выключенной музыки
        self.rect = self.image_on.get_rect(topleft=(x, y))
        self.is_playing = True  # Начальное состояние музыки (включена)

    def draw(self):
        if self.is_playing:
            window.blit(self.image_on, self.rect.topleft)
        else:
            window.blit(self.image_off, self.rect.topleft)

    def toggle(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            pygame.mixer.music.unpause()  # Возобновляем музыку
        else:
            pygame.mixer.music.pause()  # Приостанавливаем музыку


class GameSprite(pygame.sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, player_speed, scale=(20, 20)):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(player_image), scale)
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y

    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))


class Player(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed):
        super().__init__(player_image, player_x, player_y, player_speed, scale=(100, 100))
        self.speed = 3

    def disappear(self):
        self.rect.x = 0
        self.rect.y = 300  # Убедитесь, что y также устанавливается в -100

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and self.rect.x > 5:
            self.rect.x -= self.speed
        if keys[pygame.K_d] and self.rect.x < win_width - 80:
            self.rect.x += self.speed
        if keys[pygame.K_w] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[pygame.K_s] and self.rect.y < win_height - 80:
            self.rect.y += self.speed


class Star(GameSprite):
    def __init__(self, player_image, player_x, player_y):
        super().__init__(player_image, player_x, player_y, player_speed=0)

    def disappear(self):
        self.rect.x = -100
        self.rect.y = -100  # Убедитесь, что y также устанавливается в -100


class Barrier(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)


class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (100, 200, 100)  # Цвет кнопки
        self.hover_color = (150, 250, 150)  # Цвет кнопки при наведении
        self.font = font2

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(window, self.hover_color, self.rect, border_radius=10)  # Кнопка при наведении
        else:
            pygame.draw.rect(window, self.color, self.rect, border_radius=10)  # Обычная кнопка

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        window.blit(text_surface, text_rect)

    def is_clicked(self):
        mouse_click = pygame.mouse.get_pressed()
        return mouse_click[0] and self.rect.collidepoint(pygame.mouse.get_pos())


class ItemContainer:
    def __init__(self, image_path, button_text, x, y, purchased=False, price=0):
        self.image = pygame.transform.scale(pygame.image.load(image_path), (100, 100))  # Размер картинки 100x100
        self.button = Button(button_text, x + 0, y + 60, 100, 40)  # Кнопка по центру относительно картинки
        self.rect = pygame.Rect(x, y, 100, 50)  # Размер контейнера (увеличиваем для центрирования)
        self.purchased = purchased  # Добавляем состояние покупки
        self.price = price  # Добавляем цену

    def draw(self):
        # Рисуем контейнер с предметом
        pygame.draw.rect(window, (70, 70, 70), self.rect, border_radius=10)  # Фон контейнера
        pygame.draw.rect(window, (100, 70, 100), self.rect, 3, border_radius=100)  # Рамка контейнера

        # Отрисовка изображения предмета (центрируем)
        image_x = self.rect.x + (self.rect.width - self.image.get_width()) // 2
        image_y = self.rect.y + (self.rect.height - self.image.get_height()) // 2 - 20  # Смещение вверх
        window.blit(self.image, (image_x, image_y))

        # Отрисовка кнопки
        if not self.purchased:
            self.button.draw()
        else:
            # Если предмет куплен, отображаем серую кнопку с текстом "Куплено"
            pygame.draw.rect(window, (150, 150, 150), self.button.rect, border_radius=10)
            text_surface = self.button.font.render("Перейти", True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=self.button.rect.center)
            window.blit(text_surface, text_rect)

    def update(self):
        if not self.purchased and self.button.is_clicked():  # Проверяем только если не куплено
            return True  # Возвращаем True, если кнопка нажата
        elif self.purchased and self.button.is_clicked():  # Если фон куплен и на него кликнули
            return 'set_background'  # Возвращаем сигнал для установки фона
        return False


class Slider:
    def __init__(self, x, y, width, min_value=0, max_value=1, initial_value=0.5):
        self.rect = pygame.Rect(x, y, width, 20)  # Прямоугольник ползунка
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.handle_radius = 15  # Радиус круглой ручки
        self.handle_rect = pygame.Rect(
            x + int(width * (initial_value - min_value) / (max_value - min_value)) - self.handle_radius, y - 5,
            self.handle_radius * 2, self.handle_radius * 2)  # Кнопка ползунка
        self.font = pygame.font.Font(None, 36)  # Шрифт для отображения уровня громкости

    def draw(self):
        # Рисуем фон ползунка
        pygame.draw.rect(window, (255, 235, 59), self.rect)  # Чистый желтый фон ползунка

        # Рисуем линию индикатора громкости
        indicator_rect = pygame.Rect(self.rect.x, self.rect.y + 20, self.rect.width, 5)
        color_start = (255, 0, 0)  # Зеленый
        color_end = (0, 255, 0)  # Красный
        color = (
            int(color_start[0] + (color_end[0] - color_start[0]) * (self.value / self.max_value)),
            int(color_start[1] + (color_end[1] - color_start[1]) * (self.value / self.max_value)),
            int(color_start[2] + (color_end[2] - color_start[2]) * (self.value / self.max_value)),
        )
        pygame.draw.rect(window, color, indicator_rect)  # Индикатор громкости

        # Рисуем круглую ручку
        pygame.draw.circle(window, (255, 255, 255),
                           (self.handle_rect.x + self.handle_radius, self.handle_rect.y + self.handle_radius),
                           self.handle_radius)  # Белая ручка
        # Добавляем легкую тень
        pygame.draw.circle(window, (200, 200, 200),
                           (self.handle_rect.x + self.handle_radius + 2, self.handle_rect.y + self.handle_radius + 2),
                           self.handle_radius)  # Тень

        # Отображаем уровень громкости
        volume_text = self.font.render(f"{int(self.value * 100)}%", True, (0, 0, 0))
        window.blit(volume_text, (self.rect.x + self.rect.width + 10, self.rect.y - 5))

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0] and self.rect.collidepoint(mouse_pos):  # Если нажата левая кнопка мыши
            # Обновляем положение ползунка
            self.handle_rect.x = max(self.rect.x, min(mouse_pos[0] - self.handle_radius,
                                                      self.rect.x + self.rect.width - self.handle_radius))
            self.value = self.min_value + (self.handle_rect.x - self.rect.x) / (self.rect.width) * (
                    self.max_value - self.min_value)

        # Обновляем громкость музыки
        pygame.mixer.music.set_volume(self.value)


class Inventory:
    def __init__(self):
        self.visible = False
        self.alpha = 0
        self.item_containers = []
        self.close_button_rect = pygame.Rect(0, 0, 30, 30)
        self.last_toggle_time = 0
        self.toggle_delay = 0.5

        # Добавление контейнеров с изображениями и кнопками
        self.add_item('background.jpg', 'Куплено', 240, 260, purchased=True)
        self.add_item('bg2.jpg', 'Купить', 350, 260, price=price1)
        self.add_item('bg3.jpg', 'Купить', 460, 260, price=price2)

        # Кнопка для прокачки коэффициента добычи
        self.upgrade_button = Button(f"Стоимость прокачки  - {upgrade_price} ", 240, 450, 320, 40)

    def add_item(self, image_path, button_text, x, y, purchased=False, price=0):
        container = ItemContainer(image_path, button_text, x, y, purchased, price)
        self.item_containers.append(container)

    def toggle(self):
        current_time = time.time()
        if current_time - self.last_toggle_time >= self.toggle_delay:
            self.visible = not self.visible
            self.last_toggle_time = current_time

    def draw(self):
        if self.visible:
            self.alpha = min(255, self.alpha + 5)

            # Параметры инвентаря
            inventory_width = 400
            inventory_height = max(300, len(self.item_containers) * 150)
            inventory_x = win_width // 2 - inventory_width // 2
            inventory_y = win_height // 2 - inventory_height // 2

            # Рисуем фон инвентаря с закругленными углами
            pygame.draw.rect(window, (50, 50, 50), (inventory_x, inventory_y, inventory_width, inventory_height),
                             border_radius=20)
            pygame.draw.rect(window, (100, 100, 100), (inventory_x, inventory_y, inventory_width, inventory_height), 5,
                             border_radius=20)

            # Отрисовка текста "Магазин"
            shop_text = font2.render("Магазин", True, (255, 255, 255))
            shop_text_rect = shop_text.get_rect(center=(win_width // 2, inventory_y + 30))
            window.blit(shop_text, shop_text_rect)

            # Кнопка закрытия
            self.close_button_rect.topleft = (inventory_x + inventory_width - 40, inventory_y + 10)
            pygame.draw.rect(window, (255, 0, 0), self.close_button_rect, border_radius=15)
            close_text = font2.render("X", True, (255, 255, 255))
            close_text_rect = close_text.get_rect(center=self.close_button_rect.center)
            window.blit(close_text, close_text_rect)

            # Отрисовка контейнеров с предметами
            for container in self.item_containers:
                container.draw()

            # Отрисовка кнопки прокачки коэффициента добычи
            self.upgrade_button.draw()

            # Отображение текущего коэффициента добычи
            exchange_rate_text = font2.render(f"Коэффициент добычи: {exchange_rate:.1f}", True, (255, 255, 255))
            window.blit(exchange_rate_text, (240, 500))

            # Отображение сообщения о покупке
            if purchase_message:
                # Разделяем сообщение на две строки
                message_lines = purchase_message.split("!")  # Разделяем по восклицательному знаку
                if len(message_lines) > 1:
                    message1 = message_lines[0] + "!"  # Первая строка: "Недостаточно средств!"
                    message2 = message_lines[1].strip()  # Вторая строка: "Не хватает: X монет."

                    # Отрисовка первой строки
                    purchase_message_surface1 = font2.render(message1, True, (255, 0, 0))
                    message_x1 = win_width // 2 - purchase_message_surface1.get_width() // 2
                    message_y1 = inventory_y + inventory_height - 200  # Позиция выше кнопки прокачки
                    window.blit(purchase_message_surface1, (message_x1, message_y1))

                    # Отрисовка второй строки
                    purchase_message_surface2 = font2.render(message2, True, (255, 0, 0))
                    message_x2 = win_width // 2 - purchase_message_surface2.get_width() // 2
                    message_y2 = message_y1 + 30  # Ниже первой строки
                    window.blit(purchase_message_surface2, (message_x2, message_y2))

    def update(self):
        global coins, purchase_message, message_time, current_background_index, exchange_rate, upgrade_price
        if self.visible:
            if self.close_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.visible = False
                self.alpha = 0

            for container in self.item_containers:
                result = container.update()
                if result == True:
                    if not container.purchased and coins >= container.price:
                        coins -= container.price
                        container.purchased = True
                        purchase_message = "Успешно куплено!"
                        message_time = time.time()
                    else:
                        shortage = container.price - coins
                        purchase_message = f"Недостаточно средств! Не хватает: {shortage} монет."
                        message_time = time.time()

                elif result == 'set_background':
                    current_background_index = self.item_containers.index(container)

            # Обработка нажатия на кнопку прокачки коэффициента добычи
            if self.upgrade_button.is_clicked():
                if coins >= upgrade_price:
                    coins -= upgrade_price
                    exchange_rate += 0.1  # Увеличиваем коэффициент добычи
                    upgrade_price *= upgrade_multiplier  # Увеличиваем цену прокачки
                    self.upgrade_button.text = f"Стоимость прокачки  - {upgrade_price} "  # Обновляем текст кнопки
                    purchase_message = f"Коэффициент добычи увеличен до {exchange_rate:.1f}!"
                    message_time = time.time()
                else:
                    shortage = upgrade_price - coins
                    purchase_message = f"Недостаточно средств! Не хватает: {shortage} монет."
                    message_time = time.time()


class Menu:
    def __init__(self):
        self.title_font = pygame.font.Font('menu_font.ttf', 70)  # Замените на путь к вашему шрифту
        self.font = font2
        self.music_button = MusicButton(win_width - 70, win_height - 70)  # Позиция кнопки музыки
        self.title_font = pygame.font.Font('menu_font.ttf', 70)  # Замените на путь к вашему шрифту
        self.font = font2
        self.music_button = MusicButton(win_width - 70, win_height - 70)  # Позиция кнопки музыки
        self.songs = ['X1.mp3', 'X.mp3', 'X1.mp3']  # Хранилище песен
        self.current_song_index = 0
        pygame.mixer.music.load(self.songs[self.current_song_index])  # Загружаем первую песню
        pygame.mixer.music.play(-1)

    def main_menu(self):
        title_text = self.title_font.render("Симулятор фермы", True, (0, 0, 0))
        screen = pygame.display.set_mode((win_width, win_height))
        play_button = Button("Играть", win_width // 2 - 100, win_height // 2 - 10, 200, 40)
        settings_button = Button("Настройки", win_width // 2 - 100, win_height // 2 + 50, 200, 40)
        exit_button = Button("Выход", win_width // 2 - 100, win_height // 2 + 110, 200, 40)

        while True:
            window.blit(background, (0, 0))
            screen.fill(color)
            window.blit(title_text, (win_width // 2 - title_text.get_width() // 2, win_height // 2 - 200))
            play_button.draw()
            settings_button.draw()
            exit_button.draw()
            self.music_button.draw()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if play_button.is_clicked():
                    return  # Переход к игровому процессу
                if settings_button.is_clicked():
                    self.setings()  # Переход к меню настроек
                if exit_button.is_clicked():
                    pygame.quit()
                    sys.exit()
                if self.music_button.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                    self.music_button.toggle()

            pygame.display.update()

    def setings(self):
        title_text = self.title_font.render("Настройки ", True, (0, 0, 0))
        info_button = Button("Управление", win_width // 2 - 100, win_height // 2 - 10, 200, 40)
        muz_button = Button("Музыка и звуки", win_width // 2 - 100, win_height // 2 + 50, 200, 40)
        save_button = Button("В меню", win_width // 2 - 100, win_height // 2 + 200, 200, 40)

        while True:
            window.blit(background, (0, 0))
            window.fill(color)
            muz_button.draw()
            window.blit(title_text, (win_width // 2 - title_text.get_width() // 2, win_height // 2 - 200))

            info_button.draw()
            save_button.draw()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if save_button.is_clicked():
                    return  # Возврат в главное меню
                if info_button.is_clicked():
                    self.display_controls()  # Переход к меню настроек
                if muz_button.is_clicked():
                    self.display_music_info()
                if self.music_button.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                    self.music_button.toggle()
            pygame.display.update()

    def display_controls(self):
        input_boxes = []
        input_labels = [
            "Движение вверх: ",
            "Движение вниз: ",
            "Движение влево: ",
            "Движение вправо: ",
            "Инвентарь: ",
            "Сбор урожая: ",
            "Обмен на монеты: ",
            "Выход в меню: "
        ]
        default_keys = [
            controls['up'],
            controls['down'],
            controls['left'],
            controls['right'],
            controls['inventory'],
            controls['harvest'],
            controls['exchange'],
            controls['exit']
        ]

        for label, key in zip(input_labels, default_keys):
            input_boxes.append((label, pygame.key.name(key)))

        save_button = Button("Назад", win_width // 2 - 100, win_height // 2 + 200, 200, 40)

        while True:
            window.fill((255, 193, 37))  # Очистка экрана
            for i, (label, key_name) in enumerate(input_boxes):
                text_surface = font2.render(f"{label} {key_name}", True, (0, 0, 0))
                window.blit(text_surface, (50, 100 + i * 40))

            save_button.draw()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if save_button.is_clicked():
                    return  # Возврат в главное меню

            pygame.display.update()

    def display_music_info(self):
        music_info_text = self.font.render("Музыка и звуки", True, (0, 0, 0))
        window.blit(music_info_text, (win_width // 2 - music_info_text.get_width() // 2, 100))
        save_button = Button("Назад", win_width // 2 - 100, win_height // 2 + 250, 200, 40)
        music_control_text = self.font.render("Нажмите на кнопку для включения/выключения музыки", True, (0, 0, 0))
        music_control_text1 = self.font.render("Изменение фоновой музыки", True, (0, 0, 0))
        window.blit(music_control_text, (50, 150))

        # Создаем и обновляем ползунок
        volume_slider = Slider(win_width // 2 - 150, 300, 300)  # Выровняем ползунок по центру
        volume_slider.draw()

        # Загрузка изображений для кнопок переключения музыки
        left_arrow_image = pygame.image.load('left.png')  # Замените на путь к вашему изображению
        right_arrow_image = pygame.image.load('right.png')  # Замените на путь к вашему изображению
        current_song_image = pygame.image.load('musical-note.png')  # Замените на путь к вашему изображению

        # Кнопки переключения музыки
        left_button_rect = left_arrow_image.get_rect(center=(win_width // 2 - 50, 510))
        right_button_rect = right_arrow_image.get_rect(center=(win_width // 2 + 60, 505))

        # Отображаем текущее изображение песни
        window.blit(current_song_image, (win_width // 2 - current_song_image.get_width() // 2, 300))

        # Переменная для отслеживания времени последнего клика
        last_click_time = 0
        click_delay = 0.5  # Задержка между кликами в секундах

        while True:
            volume_slider.update()  # Обновляем состояние ползунка

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if save_button.is_clicked():
                    return

            # Получаем текущее время
            current_time = time.time()

            # Обработка нажатий на кнопки переключения музыки
            if left_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                if current_time - last_click_time > click_delay:  # Проверяем задержку
                    self.current_song_index = (self.current_song_index - 1) % len(
                        self.songs)  # Переключаем на предыдущую песню
                    pygame.mixer.music.load(self.songs[self.current_song_index])
                    pygame.mixer.music.play(-1)
                    last_click_time = current_time  # Обновляем время последнего клика

            if right_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                if current_time - last_click_time > click_delay:  # Проверяем задержку
                    self.current_song_index = (self.current_song_index + 1) % len(
                        self.songs)  # Переключаем на следующую песню
                    pygame.mixer.music.load(self.songs[self.current_song_index])
                    pygame.mixer.music.play(-1)
                    last_click_time = current_time  # Обновляем время последнего клика

            # Отрисовываем всё
            window.fill(color)
            save_button.draw()

            window.blit(music_info_text, (win_width // 2 - music_info_text.get_width() // 2, 100))
            window.blit(music_control_text, (50, 150))
            window.blit(music_control_text1, (50, 400))
            volume_slider.draw()  # Рисуем ползунок
            window.blit(left_arrow_image, left_button_rect.topleft)  # Рисуем кнопку влево
            window.blit(right_arrow_image, right_button_rect.topleft)  # Рисуем кнопку вправо
            window.blit(current_song_image, (win_width // 2 - current_song_image.get_width() // 2, 480))

            pygame.display.update()


# Создание объектов игры
# Создание объектов игры
farmer = Player('farmer.png', 0, 300, 2)
# Определение позиций спрайтов для каждого фона
star_positions_background_0 = [(25, 470), (425, 560), (720, 560), (600, 560), (425, 380), (720, 380), (600, 380),
                               (60, 570)]
star_positions_background_1 = [(25, 560), (560, 560), (560, 560), (600, 560), (560, 560), (560, 560), (560, 560),
                               (560, 560)]
star_positions_background_2 = [(25, 560), (425, 560), (720, 560), (560, 560), (560, 560), (560, 560), (560, 560),
                               (560, 560)]


def initialize_background_sprites(background_index, star_positions):
    stars = [Star('star.png', x, y) for x, y in star_positions]  # Создаем звезды на основе заданных позиций
    background_sprites[background_index].extend(stars)  # Добавляем звезды к соответствующему фону


initialize_background_sprites(0, star_positions_background_0)  # Звезды для первого фона
initialize_background_sprites(1, star_positions_background_1)  # Звезды для второго фона
initialize_background_sprites(2, star_positions_background_2)  # Звезды для третьего фона
# Измененные барьеры
barriers = [
    Barrier(199, 285, 60, 10),
    Barrier(0, 285, 80, 10),
    Barrier(250, 0, 10, 291)
]

inventory = Inventory()
game = True
clock = pygame.time.Clock()
last_star_time = time.time()
time_to_next_star = 10
timer_started = False
all_stars_collected = False
countdown_timer = 0
countdown_duration = 10

# Запуск игры

menu = Menu()
menu.main_menu()
exit_button1 = Button("Выход", 10, 10, 90, 40)

while game:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_game_data()
            game = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        inventory.toggle()

    current_background_index
    # Обработка нажатия кнопки Escape
    if keys[pygame.K_ESCAPE]:
        save_game_data()
        menu.main_menu()  # Возврат в главное меню

    window.blit(background, (0, 0))
    for sprite in background_sprites[current_background_index]:
        sprite.reset()
    text_score = font2.render('Собрано урожая: ' + str(score), True, (128, 0, 128))
    window.blit(text_score, (win_width - text_score.get_width() - 10, 20))

    # Отрисовка кнопки выхода в меню
    exit_button1.draw()
    if exit_button1.is_clicked():
        menu.main_menu()  # Возврат в главное меню при нажатии на кнопку

    if inventory.visible:
        inventory.draw()
        inventory.update()
        farmer.disappear()
    else:
        original_position = farmer.rect.topleft  # Сохраняем оригинальную позицию
        farmer.update()

        # Проверка на столкновение с барьерами
        for barrier in barriers:
            if farmer.rect.colliderect(barrier.rect):
                farmer.rect.topleft = original_position  # Возвращаем игрока на оригинальную позицию, если произошло столкновение

    # Установка фона в зависимости от текущего индекса
    backgrounds = ['background.jpg', 'bg2.jpg', 'bg3.jpg']
    background = pygame.transform.scale(pygame.image.load(backgrounds[current_background_index]),
                                        (win_width, win_height))

    if keys[pygame.K_e] and score > 0 and exchange_zone_rect.collidepoint(farmer.rect.center):
        coins += exchange_rate
        score -= 1

        # Отображение сообщения о покупке

        # Проверяем, прошло ли 3 секунды с момента показа сообщения
        if time.time() - message_time > message_duration:
            purchase_message = ""  # Скрываем сообщение

    # Проверка на сбор звезд
    all_stars_collected = True  # Предполагаем, что все звезды собраны
    for star in background_sprites[current_background_index]:  # Изменено на использование background_sprites
        if star.rect.x != -100:  # Если звезда на экране
            all_stars_collected = False  # Найдена звезда, значит не все собраны
            if farmer.rect.colliderect(star.rect) and keys[pygame.K_f]:
                score += 1
                star.disappear()

    # Если все звезды собраны, запускаем таймер
    if all_stars_collected:
        countdown_timer += 1 / FPS  # Увеличиваем таймер на 1/FPS
        if countdown_timer >= countdown_duration:
            # Время вышло, создаем звезды снова
            for i, star in enumerate(background_sprites[current_background_index]):
                if current_background_index == 0:
                    star.rect.x, star.rect.y = star_positions_background_0[i]
                elif current_background_index == 1:
                    star.rect.x, star.rect.y = star_positions_background_1[i]
                elif current_background_index == 2:
                    star.rect.x, star.rect.y = star_positions_background_2[i]
            countdown_timer = 0  # Сбрасываем таймер

    if timer_started:
        remaining_time = max(0, int(time_to_next_star - (time.time() - last_star_time)))
        timer_text = font2.render(f'До нового сбора: {remaining_time} сек', True, (255, 0, 0))
        window.blit(timer_text, (10, 85))
        if remaining_time == 0:
            timer_started = False

    farmer.reset()  # Сбрасываем позицию фермера для отрисовки
    for sprite in background_sprites[current_background_index]:
        sprite.reset()
    for star in background_sprites[current_background_index]:  # Изменено на использование background_sprites
        if star.rect.x != -100:
            star.reset()  # Отрисовка звезд на экране

    current_time = time.time()
    if not timer_started and current_time - last_star_time >= time_to_next_star:
        for star in background_sprites[current_background_index]:  # Изменено на использование background_sprites
            if star.rect.x == -100:
                star.rect.x = star_positions_background_0[background_sprites[current_background_index].index(star)][0]
                star.rect.y = star_positions_background_0[background_sprites[current_background_index].index(star)][1]
        last_star_time = current_time
        timer_started = True

    text_coins = font2.render('Баланс: ' + str(coins), True, (128, 0, 128))
    window.blit(text_coins, (10, 55))

    pygame.display.update()
    clock.tick(FPS)

# Сохранение данных перед выходом
save_game_data()
pygame.quit()
sys.exit()
