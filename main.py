import pygame.sprite
import pygame
import random, time, pymunk, sys
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame import mixer
import asyncio
from aiohttp import web
mixer.init()
pygame.init()
loop = asyncio.get_event_loop()
# pygame screen
screenWidth, screenHeight = 700, 700
screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)
pygame.display.set_caption("Color Run Down")
# gravity
space = pymunk.Space()
space.gravity = (0, 1000)
# window
def changeWindow(space, screenWidth, screenHeight):
    window_left = pymunk.Segment(space.static_body, (0, 0), (0, screenHeight), 2)
    window_right = pymunk.Segment(space.static_body, (screenWidth, 0), (screenWidth, screenHeight), 2)
    window_bottom = pymunk.Segment(space.static_body, (0, screenHeight), (screenWidth, screenHeight), 2)
    space.add(window_left, window_right, window_bottom)
    # Remove existing segments (if any)
    for shape in space.shapes:
        if isinstance(shape, pymunk.Segment):
            space.remove(shape)
    # Add the new segments
    space.add(window_left, window_right, window_bottom)
# Call changeWindow() with the initial screen dimensions
changeWindow(space, screenWidth, screenHeight)
# colors
TextColor = (0, 0, 0)
BLACK = (0,0,0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
# background
clock = pygame.time.Clock()
background_colour = WHITE
screen.fill(background_colour)
pygame.display.flip()
# text
class Text:
    def __init__(self, text, font_size, color, position):
        self.text = text
        self.font_size = font_size
        self.color = color
        self.position = position
        self.font = pygame.font.Font(None, self.font_size)  # You can specify a font file or use None for default font
        self.rendered_text = None

    def update(self, new_text):
        self.text = new_text
        self.rendered_text = None  # Clear the rendered text to update it

    def render(self, screen):
        if self.rendered_text is None:
            self.rendered_text = self.font.render(self.text, True, self.color)
        screen.blit(self.rendered_text, self.position)
endGame = Text("Sorry, you lost the game! would you like to restart?", 36, TextColor, ((screenHeight / 2) - 300,(screenWidth / 2) - 90))
currentXP = 0
currentLevel = 1
xp = Text("XP: ", 36, TextColor, ((screenHeight / 2) + 100,25))
# buttons
class Button:
    def __init__(self, x, y, width, height, text, active_color, inactive_color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.color = self.inactive_color
        self.font_size = min(self.width // len(self.text) + 10, self.height)
        self.font = pygame.font.Font(None, self.font_size)
        self.clicked = False

    def update_position(self, screenWidth, screenHeight):
        self.x = screenWidth // 2 - self.width // 2
        self.y = screenHeight // 2 - self.height // 2

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if self.x < mouse_pos[0] < self.x + self.width and self.y < mouse_pos[1] < self.y + self.height:
            self.color = self.active_color
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.clicked = True  # Add this line to set the 'clicked' attribute to True
                    self.color = self.active_color
        else:
            self.color = self.inactive_color

    def reset(self):
        self.clicked = False
        self.color = self.active_color
MenuButton = Button(10, 10, 100, 40, "menu", RED, GREEN)
ShopButton = Button(130, 10, 100, 40, "Shop", RED, GREEN)
LevelUpButton = Button(250, 10, 100, 40, "Level Up", RED, GREEN)
RestartButton = Button((screenHeight / 2),(screenWidth / 2), 100, 40, "Restart", GREEN, RED)
# Circle
currently_dragged_circle = None
circle_group = pygame.sprite.Group()
rect_width = 2 * 15
rect_height = 2 * 15
class Circle(pygame.sprite.Sprite):
    def __init__(self, mass, radius, position=(0, 0)):
        super().__init__()
        self.radius = radius
        self.mass = mass
        self.position = position
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
        self.body.position = position  # Set the initial position
        self.shape = pymunk.Circle(self.body, self.radius)
        space.add(self.body, self.shape)
        self.shape.collision_type = 1
        self.shape.elasticity = 0.5
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
        self.newColor = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
        pygame.draw.circle(self.image, self.newColor + (255,), (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.center = self.body.position  # Set the initial position
        self.dragging = False

    def update(self):
        global screenWidth, screenHeight
        new_x = max(self.radius, min(self.body.position.x, screenWidth - self.radius))
        new_y = max(self.radius, min(self.body.position.y, screenHeight - self.radius))
        self.rect.center = int(self.body.position.x), int(self.body.position.y)
        self.body.position = pymunk.Vec2d(new_x, new_y)
        if self.dragging:
            # Apply gravity when not dragging
            self.body.velocity = (0, 0)

    def handle_event(self, event):
        global currently_dragged_circle, rect_height, rect_width
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check if the mouse click is inside the circle
                if self.rect.collidepoint(event.pos):
                    currently_dragged_circle = self
                    self.dragging = True
                    self.drag_offset = (self.body.position.x - event.pos[0], self.body.position.y - event.pos[1])
            if event.button == 3:
                # Check if the mouse click is inside the circle
                if self.rect.collidepoint(event.pos):
                    invisible_rect = pygame.Rect(0, 0, rect_width, rect_height)
                    invisible_rect.center = self.body.position
                    circles_to_remove = []
                    for circle in circle_group:
                        if invisible_rect.collidepoint(circle.body.position):
                            space.remove(circle.body, circle.shape)
                            circle_group.remove(circle)
                            all_sprites_list.remove(circle)
                            circles_to_remove.append(circle)
                            LevelUp()
                            
                    for circle in circles_to_remove:
                        circle_group.remove(circle)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Move the circle with the mouse
                new_x = event.pos[0] + self.drag_offset[0]
                new_y = event.pos[1] + self.drag_offset[1]
                self.body.position = (new_x, new_y)
# Shop
class ShopWindow:
    def __init__(self, width, height, position=(0, 0)):
        self.width = width
        self.height = height
        self.x, self.y = position[0], position[1]
        self.visible = False
        self.CloseShopButton = Button(self.x + 2, self.y + 2, 40, 40, "X", RED, RED)
        self.text = "Shop   {}xp"
        self.font_size = min(self.width // len(self.text), self.height // 10)
        self.font = pygame.font.Font(None, self.font_size)
        self.not_enough_money_timer = 0
        self.selected_button = None
        self.BackgroundColor = WHITE
        # prices
        self.BACKGROUND_COLOR_PRICE = 25
        self.WINDOW_BACKGROUND_COLOR_PRICE = 50
        self.TEXT_COLOR_PRICE = 10
        # error
        self.NotEnoughMoney = Text("sorry, you don't have enough XP", 36, TextColor, ((screenWidth / 2) - 200,100))
        # store buttons
        self.styleList = []
        self.buttonList = []
        # change background color
        self.Background = Text("What background color would you like? 25xp", 36, TextColor, (10,160))
        for x in range(6):
            color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
            item_name = "{}".format(color)
            Items = Button(10 + (x * 110), 200, 100, 40,item_name, RED, color)
            self.styleList.append(color)
            self.buttonList.append(Items)
        # change window background
        self.WindowBackground = Text("What window background color would you like? 50xp", 36, TextColor, (10,265))
        for x in range(6):
            color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
            item_name = "{}".format(color)
            Items = Button(10 + (x * 110), 300, 100, 40,item_name, RED, color)
            self.styleList.append(color)
            self.buttonList.append(Items)
        # change text colors
        self.ColorText = Text("What color text would you like? 10xp", 36, TextColor, (10,365))
        for x in range(6):
            color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
            item_name = "{}".format(color)
            Items = Button(10 + (x * 110), 400, 100, 40,item_name, RED, color)
            self.styleList.append(color)
            self.buttonList.append(Items)
        # sound
        self.storeWindow_open_sound = pygame.mixer.Sound(r"516704__matrixxx__a-zombie-trying-to-grab-you.mp3")
        self.storeWindow_open_sound_played = False

    def update(self):
        global screenHeight, screenWidth
        self.width = screenWidth
        self.height = screenHeight
        # Update the position of the close button
        self.CloseShopButton.x = self.x + self.width - 42
        self.CloseShopButton.y = self.y + 2
    
    def play_sound_effect(self, filename):
        global soundEffect_volume
        # Play a sound effect for an affordable action
        affordable_sound = pygame.mixer.Sound(filename)
        affordable_sound.set_volume(soundEffect_volume)  # Set the volume here
        affordable_sound.play()
                
    def NotEnoughMoneyMessage(self):
        global soundEffect_volume
        if self.not_enough_money_timer > 0:
            self.not_enough_money_timer -= 1
            self.NotEnoughMoney.render(screen)
                
    def draw(self):
        global currentXP
        if self.visible:
            pygame.draw.rect(screen, self.BackgroundColor, (self.x - 2, self.y - 2, self.width + 4, self.height + 4))
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height), 2)
            self.CloseShopButton.draw(screen)
            self.Background.render(screen)
            self.WindowBackground.render(screen)
            self.ColorText.render(screen)
            # draw buttons
            for Item in self.buttonList:
                Item.draw(screen)
            # Draw the "Not Enough Money" message on top of buttons
            self.NotEnoughMoneyMessage()
            text_surface = self.font.render(self.text.format(currentXP), True, TextColor)
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 10))
            screen.blit(text_surface, text_rect)

            if not self.storeWindow_open_sound_played:
                self.storeWindow_open_sound.play()
                self.storeWindow_open_sound_played = True

    def handle_event(self, event):
        global background_colour, currentXP, shopWindow, menuWindow, levelUpWindow, TextColor, endGame, xp
        if self.visible:
            self.CloseShopButton.handle_event(event)
            if self.CloseShopButton.clicked:
                self.visible = False
                self.CloseShopButton.clicked = False
                self.selected_button = None
                self.storeWindow_open_sound_played = False
            # change theme
            for Item in self.buttonList:
                Item.handle_event(event)
                if Item.clicked:
                    self.selected_button = Item
                    selected_index = self.buttonList.index(self.selected_button)
                    # Check the stored position information
                    if self.selected_button.y == 200 and currentXP >= self.BACKGROUND_COLOR_PRICE:
                        background_colour = self.styleList[selected_index]
                        currentXP -= self.BACKGROUND_COLOR_PRICE
                        self.play_sound_effect(r"320654__rhodesmas__level-up-02.mp3")
                    elif self.selected_button.y == 200 and currentXP < self.BACKGROUND_COLOR_PRICE:
                        self.not_enough_money_timer = 100
                        self.play_sound_effect(r"527491__hipstertypist__error-sound.mp3")
                    elif self.selected_button.y == 300 and currentXP >= self.WINDOW_BACKGROUND_COLOR_PRICE:
                        shopWindow.BackgroundColor = self.styleList[self.buttonList.index(Item)]
                        menuWindow.background_color = self.styleList[self.buttonList.index(Item)]
                        levelUpWindow.BackgroundColor = self.styleList[self.buttonList.index(Item)]
                        currentXP -= self.WINDOW_BACKGROUND_COLOR_PRICE
                        self.play_sound_effect(r"320654__rhodesmas__level-up-02.mp3")
                    elif self.selected_button.y == 300 and currentXP < self.WINDOW_BACKGROUND_COLOR_PRICE:
                        self.not_enough_money_timer = 100
                        self.play_sound_effect(r"527491__hipstertypist__error-sound.mp3")
                    elif self.selected_button.y == 400 and currentXP >= self.TEXT_COLOR_PRICE:
                        TextColor = self.styleList[self.buttonList.index(Item)]
                        endGame.color = TextColor
                        xp.color = TextColor
                        shopWindow.NotEnoughMoney.color = TextColor
                        levelUpWindow.NotEnoughLevels.color = TextColor
                        menuWindow.message.color = TextColor
                        # Modify the text elements within shopWindow
                        self.Background.color = TextColor
                        self.WindowBackground.color = TextColor
                        self.ColorText.color = TextColor
                        # Modify the text elements within levelUpWindow
                        levelUpWindow.row.color = TextColor
                        # Modify the text elements within menuWindow
                        menuWindow.sound.color = TextColor
                        menuWindow.sound_effects.color = TextColor
                        menuWindow.frame_rate.color = TextColor
                        currentXP -= 5
                        self.play_sound_effect(r"320654__rhodesmas__level-up-02.mp3")
                    elif self.selected_button.y == 400 and currentXP < self.TEXT_COLOR_PRICE:
                        self.not_enough_money_timer = 100
                        self.play_sound_effect(r"527491__hipstertypist__error-sound.mp3")
                    self.selected_button.clicked = False
shopWindow = ShopWindow(screenHeight, screenWidth, position=(0, 0))
# Level up
class LevelUpWindow:
    def __init__(self, width, height, position=(0, 0)):
        self.width = width
        self.height = height
        self.x, self.y = position[0], position[1]
        self.visible = False
        self.CloseLevelUpButton = Button(self.x + 2, self.y + 2, 40, 40, "X", RED, RED)
        self.text = "Level up   {} Levels"
        self.font_size = min(self.width // len(self.text), self.height // 10)
        self.font = pygame.font.Font(None, self.font_size)
        self.not_enough_money_timer = 0
        self.selected_button = None
        self.BackgroundColor = WHITE
        self.sound_effect_played = False
        self.level_cost = 6   # Levels needed per button increase
        self.NotEnoughLevels = Text("Sorry, you don't have enough Levels", 36, TextColor, ((screenWidth / 2) - 200, 100))
        self.rowButtonList = []
        self.row = Text("How big would you like the row to be? 6 Levels per button", 36, TextColor, (10, 160))
        # create buttons
        for x in range(6):
            label = str(6 + x * self.level_cost)
            Items = Button(10 + (x * 110), 200, 100, 40,label, RED, GREEN)
            self.rowButtonList.append(Items)
        # sound
        self.levelWindow_open_sound = pygame.mixer.Sound(r"516704__matrixxx__a-zombie-trying-to-grab-you.mp3")
        self.levelWindow_open_sound_played = False

    def update(self):
        global screenHeight, screenWidth
        self.width = screenWidth
        self.height = screenHeight
        self.CloseLevelUpButton.x = self.x + self.width - 42
        self.CloseLevelUpButton.y = self.y + 2

    def play_sound_effect(self, filename):
        global soundEffect_volume
        # Play a sound effect for an affordable action
        affordable_sound = pygame.mixer.Sound(filename)
        affordable_sound.set_volume(soundEffect_volume)  # Set the volume here
        affordable_sound.play()

    def NotEnoughMoneyMessage(self):
        global soundEffect_volume
        if self.not_enough_money_timer > 0:
            self.not_enough_money_timer -= 1
            self.NotEnoughLevels.render(screen)

    def draw(self):
        global currentLevel
        if self.visible:
            pygame.draw.rect(screen, self.BackgroundColor, (self.x - 2, self.y - 2, self.width + 4, self.height + 4))
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height), 2)
            self.CloseLevelUpButton.draw(screen)
            # draw buttons for levels
            for Item in self.rowButtonList:
                Item.draw(screen)

            self.NotEnoughMoneyMessage()
            text_surface = self.font.render(self.text.format(currentLevel), True, TextColor)
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 10))
            screen.blit(text_surface, text_rect)

            if not self.levelWindow_open_sound_played:
                self.levelWindow_open_sound.play()
                self.levelWindow_open_sound_played = True

    def handle_event(self, event):
        global currentLevel
        if self.visible:
            self.CloseLevelUpButton.handle_event(event)
            if self.CloseLevelUpButton.clicked:
                self.visible = False
                self.CloseLevelUpButton.clicked = False
                self.levelWindow_open_sound_played = False
            # levels
            for Item in self.rowButtonList:
                Item.handle_event(event)
                if Item.clicked:
                    self.selected_button = Item
                    selected_index = self.rowButtonList.index(self.selected_button)
                    if currentLevel >= 10:
                        currentLevel -= 10
                        self.play_sound_effect(r"320654__rhodesmas__level-up-02.mp3")
                    else:
                        self.not_enough_money_timer = 100
                        self.play_sound_effect(r"527491__hipstertypist__error-sound.mp3")
                    Item.clicked = False
levelUpWindow = LevelUpWindow(screenHeight, screenWidth, (0, 0))
#menu
class MenuWindow:
    def __init__(self, width, height, position=(0, 0)):
        self.width = width
        self.height = height
        self.x, self.y = position[0], position[1]
        self.visible = False
        self.close_button = Button(self.x + 2, self.y + 2, 40, 40, "X", RED, RED)
        self.title = "Menu"
        self.font_size = min(self.width // len(self.title), self.height // 10)
        self.font = pygame.font.Font(None, self.font_size)
        self.background_color = WHITE
        # text
        self.message = Text("your changes will apply when you exit the window", 36, TextColor, ((screenWidth / 2) - 300,100))
        # Sliders
        self.sound = Text("Music", 36, TextColor, (10, 160))
        self.sound_slider = Slider(screen, 10, 200, 200, 10, min=0, max=1.0, step=0.1, initial=1.0)
        self.sound_output = TextBox(screen, 220, 170, 50, 50, fontSize=30)
        self.sound_output.disable()

        self.sound_effects = Text("Sound Effects", 36, TextColor, (10, 260))
        self.sound_effects_slider = Slider(screen, 10, 300, 200, 10, min=0, max=1.0, step=0.1, initial=1.0)
        self.sound_effects_output = TextBox(screen, 220, 270, 50, 50, fontSize=30)
        self.sound_effects_output.disable()

        self.frame_rate = Text("Frame Rate", 36, TextColor, (10, 360))
        self.frame_rate_slider = Slider(screen, 10, 400, 128, 10, min=1, max=64, step=1, initial=100)
        self.frame_rate_output = TextBox(screen, 148, 370, 50, 50, fontSize=30)
        self.frame_rate_output.disable()
        # sound
        self.menu_open_sound = pygame.mixer.Sound(r"516704__matrixxx__a-zombie-trying-to-grab-you.mp3")
        self.menu_open_sound_played = False

    def update(self):
        global screenHeight, screenWidth
        self.width = screenWidth
        self.height = screenHeight
        self.close_button.x = self.x + self.width - 42
        self.close_button.y = self.y + 2

    def draw(self):
        if self.visible:
            pygame.draw.rect(screen, self.background_color, (self.x - 2, self.y - 2, self.width + 4, self.height + 4))
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height), 2)
            self.close_button.draw(screen)
            self.sound.render(screen)
            self.sound_effects.render(screen)
            self.frame_rate.render(screen)
            self.message.render(screen)

            self.sound_output.setText(round(self.sound_slider.getValue(), 2))
            self.sound_effects_output.setText(round(self.sound_effects_slider.getValue(), 2))
            self.frame_rate_output.setText(self.frame_rate_slider.getValue())

            text_surface = self.font.render(self.title, True, TextColor)
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 10))
            screen.blit(text_surface, text_rect)

            if not self.menu_open_sound_played:
                self.menu_open_sound.play()
                self.menu_open_sound_played = True
            
    def handle_event(self, event):
        global game_paused, frameRate, Background_volume, soundEffect_volume
        if self.visible:
            self.close_button.handle_event(event)
            pygame_widgets.update(event)

            if self.close_button.clicked:
                self.visible = False
                self.close_button.clicked = False
                game_paused = False
                Background_volume = self.sound_slider.getValue()
                BackgroundMusic.set_volume(Background_volume)
                game_over_music.set_volume(Background_volume)
                soundEffect_volume = self.sound_effects_slider.getValue()  # Update sound effect volume here
                frameRate = self.frame_rate_slider.getValue()
                self.menu_open_sound_played = False
menuWindow = MenuWindow(screenHeight, screenWidth, (0, 0))
# drop
time = 0
def Drop():
    global time
    time += 1
    if time % 100 == 0:
        for item in range(int(random.triangular(1,10,3))):
            circle = Circle(1, 15,(random.randint(0,screenWidth),16))
            circle_group.add(circle)
            all_sprites_list.add(circle)
# game over
gameOver_soundEffect_Played = False
def play_game_over_sound_effect():
    global soundEffect_volume,gameOver_soundEffect_Played
    if not gameOver_soundEffect_Played:
        game_over_sound = pygame.mixer.Sound(r"162465__kastenfrosch__lostitem.mp3")  # Replace "game_over_sound.wav" with your sound file
        game_over_sound.set_volume(soundEffect_volume)
        game_over_sound.play()
        gameOver_soundEffect_Played = True
# restart
def RestartLevel():
    global circle_group, all_sprites_list, currentXP, currentLevel, background_colour, TextColor
    for circle in circle_group:
        space.remove(circle.body, circle.shape)
    circle_group.empty()
    all_sprites_list.empty()
    # Reset button states
    ShopButton.reset()
    LevelUpButton.reset()
    MenuButton.reset()
    # Reset window states
    shopWindow.visible = False
    levelUpWindow.visible = False
    menuWindow.visible = False
    # return defult
    shopWindow.BackgroundColor = WHITE
    menuWindow.background_color = WHITE
    levelUpWindow.BackgroundColor = WHITE
    background_colour = WHITE
    # text
    TextColor = BLACK
    endGame.color = TextColor
    xp.color = TextColor
    shopWindow.NotEnoughMoney.color = TextColor
    levelUpWindow.NotEnoughLevels.color = TextColor
    menuWindow.message.color = TextColor
    # Modify the text elements within shopWindow
    shopWindow.Background.color = TextColor
    shopWindow.WindowBackground.color = TextColor
    shopWindow.ColorText.color = TextColor
    # Modify the text elements within levelUpWindow
    levelUpWindow.row.color = TextColor
    # Modify the text elements within menuWindow
    menuWindow.sound.color = TextColor
    menuWindow.sound_effects.color = TextColor
    menuWindow.frame_rate.color = TextColor
    # reset value
    currentXP = 0
    currentLevel = 1

def restart_game():
    global game_over_music_playing, game_play_music_playing
    RestartLevel()
    game_over_music.stop()
    game_over_music_playing = False
    BackgroundMusic.play(-1)
    game_play_music_playing = True
#level up
def LevelUp():
    global currentXP, currentLevel
    currentXP += 1
    if currentXP == (currentLevel * 100):
        currentLevel += 1
        currentXP = 0

 # loop
all_sprites_list = pygame.sprite.Group()
shopWindow.visible = False
levelUpWindow.visible = False
running = True
game_paused = False
# settings
frameRate = 64
Background_volume = 1.0
soundEffect_volume = 1.0

game_play_music_playing = False
BackgroundMusicPath = "ambient-piano-ampamp-strings-10711.mp3"
BackgroundMusic = pygame.mixer.Sound(BackgroundMusicPath)
BackgroundMusic.set_volume(Background_volume)
# game lost
game_over_music_playing = False
game_over_music_path = r"lost-ambient-lofi-sad-background-music-5802.mp3"
game_over_music = pygame.mixer.Sound(game_over_music_path)
game_over_music.set_volume(Background_volume)

async def handle(request):
    return web.Response(text="Hello, World!")
        
async def game_loop():
    global running, screen, game_over_music, game_over_music_playing, game_play_music_playing, game_paused, screenWidth, screenWidth
    asyncio.create_task(handle(game_loop()))
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screenWidth, screenHeight = event.size
                screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)
                changeWindow(space, screenWidth, screenHeight)
                menuWindow.message.position = ((screenWidth / 2) - 300,100)
                RestartButton.update_position(screenWidth, screenHeight)
            for circle in circle_group:
                circle.handle_event(event)
            # ShopButton,LevelUpButton,menu
            ShopButton.handle_event(event)
            LevelUpButton.handle_event(event)
            MenuButton.handle_event(event)
            RestartButton.handle_event(event)
            if ShopButton.clicked:
                shopWindow.visible = not shopWindow.visible  
                ShopButton.clicked = False  # Reset the ShopButton click state
            if LevelUpButton.clicked:
                levelUpWindow.visible = not levelUpWindow.visible
                LevelUpButton.clicked = False
            if MenuButton.clicked:
                menuWindow.visible = not menuWindow.visible 
                MenuButton.clicked = False
                game_paused = True
        # man game
        screen.fill(background_colour)
        xp.update("Level: {} XP: {}".format(currentLevel,currentXP))
        # sprites
        circle_group.update()
        circle_group.draw(screen)
        all_sprites_list.update()
        all_sprites_list.draw(screen)
        ShopButton.draw(screen)
        LevelUpButton.draw(screen)
        MenuButton.draw(screen)
        # restart game
        # Handle restart logic
        restart_required = False
        for circle in circle_group:
            if len(circle_group) >= 1000 or (not circle.dragging and circle.body.position[1] - circle.radius <= 0):
                restart_required = True
                break
        if restart_required:
            if not game_over_music_playing:
                game_over_music.play(-1)
                game_over_music_playing = True
                BackgroundMusic.stop()
                game_play_music_playing = False

            play_game_over_sound_effect()
            endGame.render(screen)
            RestartButton.handle_event(event)
            RestartButton.draw(screen)
            if RestartButton.clicked:
                await restart_game()
                RestartButton.reset()
        else:
            if game_over_music_playing:
                game_over_music.stop()
                game_over_music_playing = False

            if not game_play_music_playing:
                BackgroundMusic.play(-1)
                game_play_music_playing = True

            if not game_paused:
                game_over_music.stop()
                game_over_music_playing = False
                Drop()
                space.step(1/60)
        xp.render(screen)
        # windows
        if shopWindow.visible:
            shopWindow.draw()
            shopWindow.handle_event(event)
            shopWindow.update()
        if levelUpWindow.visible:
            levelUpWindow.handle_event(event)
            levelUpWindow.draw()
            levelUpWindow.update()
        if menuWindow.visible:
            menuWindow.draw()
            menuWindow.handle_event(event)
            menuWindow.update()
        # update
        pygame.display.update()
        clock.tick(frameRate)
        await asyncio.sleep(0)

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    game_task = asyncio.create_task(game_loop())
    web_runner = web.AppRunner(app)
    await web_runner.setup()
    site = web.TCPSite(web_runner, 'localhost', 8000)
    await site.start()
    await game_task

asyncio.run(main())
