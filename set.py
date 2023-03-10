import pygame
import random
from dataclasses import dataclass
from enum import Enum

# === VARIABELEN ===
SCREEN_WIDTH = 1280 # pixels
SCREEN_HEIGHT = 720 # pixels

FPS = 60

SECONDS_TO_CHOOSE_SET = 15
SECONDS_BEFORE_CAP_SET = 5
PC_PICKING_TIME = 0.5 # seconds

# === Enums ===
class GamePhase(Enum):
    MENU = 0
    GAME_START = 1
    SETS_VINDEN = 2
    SET_INNEN = 3
    DOORSCHUIVEN = 4
    AANVULLEN = 5
    PC_PICKING_CARDS = 6
    AFLEGGEN = 7
    EINDE = 8
    
class Colours(Enum):
    # (R, G, B) of (R, G, B, A)
    BACKGROUND = (221, 221, 221)
    TRANSPARENT = (0, 0, 0, 0)
    
    YOU = (0, 0, 255)
    PC = (255, 0, 0)

# === PROGRAMMEERVARIABELEN ===
# game_objects zijn de objects met de functies tick() en render(surface).
# Ook kunnen ze een int z_index hebben.
game_objects = []

# Objects met een mouseDown(position) en mouseUp(position).
mouse_listeners = []

selected_cards = []

layers = []

total_ticks_since_phase_change = 0
game_phase = GamePhase.MENU
pc_picking_ticks = int(PC_PICKING_TIME * FPS)

# === FUNCTIES ===
def isEenSet(kaarten):
    kaart1, kaart2, kaart3 = kaarten
    for e1, e2, e3 in zip(kaart1.getValues(), kaart2.getValues(), kaart3.getValues()):
        if (e1 + e2 + e3) % 3 != 0:
            return False
    return True

def vindSets(kaarten):
    # Sorteer de kaarten op basis van ID
    kaarten = sorted(kaarten, key = lambda kaart: kaart.getID())
    combinaties = []
    # Loop over alle combinaties van twee kaarten
    for index1, kaart1 in enumerate(kaarten[:-2]):
        for index2, kaart2 in enumerate(kaarten[index1 + 1:-1]):
            # Zoek welke kaart nodig is om de set compleet te maken
            bijbehorende_eigenschappen = []
            for e1, e2 in zip(kaart1.getValues(), kaart2.getValues()):
                if e1 == e2:
                    # dan moet de overige kaart dezelfde waarde hebben
                    bijbehorende_eigenschappen.append(e1)
                else:
                    # dan moet de overige kaart de overblijvende waarde hebben
                    # bij elkaar opgeteld moeten verschillende eigenschappen altijd 6 zijn
                    bijbehorende_eigenschappen.append(6 - e1 - e2)
            kleur, vorm, vulling, aantal = bijbehorende_eigenschappen
            bijbehorende_kaart = Kaart(kleur, vorm, vulling, aantal)
            # Zoek nu deze kaart
            index3 = zoekKaart(kaarten, bijbehorende_kaart, index1 + index2 + 2, len(kaarten))
            # Als deze kaart is gevonden, dan is dit een set
            if index3 >= 0:
                kaart3 = kaarten[index3]
                combinaties.append([kaart1, kaart2, kaart3])
                    
    return combinaties

def isErEenSet(kaarten):
    combinaties = vindSets(kaarten)
    if combinaties == []:
        return False
    return True

# een functie om in een gesorteerde lijst kaarten een bepaalde kaart te vinden m.b.v. Binary Search
def zoekKaart(kaarten, kaart, linkergrens, rechtergrens):
    if linkergrens >= rechtergrens:
        return -1
    midden = (linkergrens + rechtergrens) // 2
    if kaarten[midden] == kaart:
        return midden
    if kaarten[midden].getID() > kaart.getID():
        return zoekKaart(kaarten, kaart, linkergrens, midden)
    else:
        return zoekKaart(kaarten, kaart, midden + 1, rechtergrens)

def initialize():
    global menu, grid, you, pc
    pygame.init()
    
    pygame.font.init()
    ScoreCard.SCORE_FONT = pygame.font.SysFont("Arial", ScoreCard.SCORE_FONT_SIZE, bold = True)
    ScoreCard.NAME_FONT = pygame.font.SysFont("Arial", ScoreCard.NAME_FONT_SIZE, bold = True)

    grid = Grid(20)
    
    Menu.initialize()
    menu = Menu()
    
    you = Player("YOU", Colours.YOU.value,  (20, 20))
    pc = Player("PC", Colours.PC.value, (20, 20 + VisualCard.HEIGHT + grid.card_margin))
    
    SetCard.initialize()
    
    loop()
    
def reset():
    global game_objects
    game_objects = [game_object for game_object in game_objects if type(game_object) != SetCard]
    grid.reset()
    you.score = 0
    pc.score = 0
    
def loop():
    global total_ticks_since_phase_change
    
    # Initialize screen
    clock = pygame.time.Clock()
    canvas = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Set!")
    
    current_game_phase = game_phase
    running = True
    while running:
        tick()
        for event in pygame.event.get():
            # Check if the game should quit
            if event.type == pygame.QUIT:
                running = False
                
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                for mouse_listener in mouse_listeners:
                    mouse_listener.mouseDown(pygame.mouse.get_pos())
                    
            if event.type == pygame.MOUSEBUTTONUP:
                for mouse_listener in mouse_listeners:
                    mouse_listener.mouseUp(pygame.mouse.get_pos())
        
        # Rendering
        canvas.fill(Colours.BACKGROUND.value)
        
        render(canvas)
        
        pygame.display.update()
        
        total_ticks_since_phase_change += 1
        
        if game_phase != current_game_phase:
            total_ticks_since_phase_change = 0
            current_game_phase = game_phase
        
        clock.tick(FPS)
                
    pygame.quit()
    
def tick():
    global selected_cards, game_phase, pc_set
    # Game objects
    for game_object in game_objects:
        game_object.tick()
        
    # Alle werking achter het spel
    if game_phase == GamePhase.GAME_START:
        if total_ticks_since_phase_change >= 12 * Grid.ticks_tussen_uitdelen:
            game_phase = GamePhase.SETS_VINDEN
            return
        
        if total_ticks_since_phase_change % Grid.ticks_tussen_uitdelen == 0:
            grid.nieuweKaart()
    
    if game_phase == GamePhase.AANVULLEN:
        if total_ticks_since_phase_change >= 3 * Grid.ticks_tussen_uitdelen:
            game_phase = GamePhase.SETS_VINDEN
            return
            
        if total_ticks_since_phase_change % Grid.ticks_tussen_uitdelen == 0:
            grid.nieuweKaart()
    
    if game_phase == GamePhase.DOORSCHUIVEN:
        if total_ticks_since_phase_change == 0:
            grid.doorschuiven()
        if total_ticks_since_phase_change == GlideAnimation.total_glide_ticks:
            if grid.stapel_op:
                game_phase = GamePhase.SETS_VINDEN
                return
            else:
                game_phase = GamePhase.AANVULLEN
                return
        
    if game_phase == GamePhase.SET_INNEN:
        # start the moving of cards
        if total_ticks_since_phase_change == GlideAnimation.total_glide_ticks:
            game_phase = GamePhase.DOORSCHUIVEN
            return
            
    if game_phase == GamePhase.PC_PICKING_CARDS:
        if total_ticks_since_phase_change >= 3 * pc_picking_ticks:
            for card in grid.cards:
                if card.kaart in pc_set:
                    card.pc_selected = False
                    card.chosen = True
                    card.glide(pc.score_card.position)
            pc.score += 1
            SoundPlayer.playSound("audio\\point.wav")
            game_phase = GamePhase.SET_INNEN
            return
        
        if total_ticks_since_phase_change % pc_picking_ticks == 0:
            index = total_ticks_since_phase_change // pc_picking_ticks
            kaart = pc_set[index]
            for card in grid.cards:
                if card.kaart == kaart:
                    card.pc_selected = True
            SoundPlayer.playSound("audio\\card_select.wav")
                    
    if game_phase == GamePhase.AFLEGGEN:
        if total_ticks_since_phase_change < 3 * Grid.ticks_tussen_uitdelen:
            if total_ticks_since_phase_change % Grid.ticks_tussen_uitdelen == 0:
                index = total_ticks_since_phase_change // Grid.ticks_tussen_uitdelen
                grid.cards[index].chosen = True
                grid.cards[index].glide(grid.aflegstapel_positie)
                SoundPlayer.playSound("audio\\card_place.wav")
                
        if total_ticks_since_phase_change == GlideAnimation.total_glide_ticks:
            grid.aflegstapel.texture = ImageLoader.loadImage("kaarten\\blank.gif")
            
        if total_ticks_since_phase_change >= 3 * Grid.ticks_tussen_uitdelen + GlideAnimation.total_glide_ticks:
            game_phase = GamePhase.DOORSCHUIVEN
            return
    
    if game_phase == GamePhase.SETS_VINDEN:
        if len(selected_cards) == 3:
            kaarten = [card.kaart for card in selected_cards]
            if isEenSet(kaarten):
                for card in selected_cards:
                    card.glide(you.score_card.position)
                    card.chosen = True
                you.score += 1
                SoundPlayer.playSound("audio\\point.wav")
                grid.deselectAllCards()
                game_phase = GamePhase.SET_INNEN
                return
            else:
                for card in selected_cards:
                    card.wrong_blink_tick = 0
                SoundPlayer.playSound("audio\\wrong_sound.wav")
                grid.deselectAllCards()
                
        if total_ticks_since_phase_change == SECONDS_TO_CHOOSE_SET * FPS:
            sets = vindSets(grid.getKaarten())
            if len(sets) > 0:
                grid.deselectAllCards()
                pc_set = sets[0]
                game_phase = GamePhase.PC_PICKING_CARDS
                return
                
        if total_ticks_since_phase_change >= SECONDS_BEFORE_CAP_SET * FPS:
            set_exists = isErEenSet(grid.getKaarten())
            if not set_exists:
                grid.deselectAllCards()
                if grid.stapel_op:
                    grid.aflegstapel.z_index = 10
                    game_phase = GamePhase.EINDE
                    return
                else:
                    game_phase = GamePhase.AFLEGGEN
                    return
    
    if game_phase == GamePhase.EINDE:
        if total_ticks_since_phase_change % grid.ticks_tussen_uitdelen == 0:
            index = total_ticks_since_phase_change // grid.ticks_tussen_uitdelen
            if index >= len(grid.cards):
                game_phase = GamePhase.MENU
                return
            grid.cards[index].glide(grid.aflegstapel_positie)
            SoundPlayer.playSound("audio\\card_place.wav")
                
def render(canvas):
    # Make all layers transparent
    for layer in layers:
        layer.surface.fill(Colours.TRANSPARENT.value)
        layer.used = False
    
    for game_object in game_objects:
        # Get the z-index, with a default value of 0
        if hasattr(game_object, "z_index"):
            z_index = game_object.z_index
        else:
            z_index = 0
        
        # Get the corresponding layer
        layer = None
        for potential_layer in layers:
            if potential_layer.z_index == z_index:
                layer = potential_layer
                
        # If no layer with that z-index exists yet, create one
        if layer is None:
            layer = Layer(z_index, pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32))
            layers.append(layer)
            
        # Mark this layer as still being used, so it will not be removed
        layer.used = True
            
        # Render the game object
        game_object.render(layer.surface)
    
    # Sort the layers, so that the layers with lowest z-index will be rendered first, and therefore lowest
    layers.sort(key = lambda layer: layer.z_index)
    for layer in layers:
        canvas.blit(layer.surface, (0, 0))
        
        # Remove the layer if it is no longer used
        if not layer.used:
            layers.remove(layer)

# === GAME OBJECTS ===
class VisualCard:
    WIDTH = 100
    HEIGHT = 200
    
    def __init__(self, position = (0, 0), filename = "blank"):
        self.position = position
        self.gliding = False
            
        self.texture = ImageLoader.loadImage(f"kaarten\\{filename}.gif")
        
    def tick(self):
        # Handle Glide Animation
        if self.gliding:
            self.glide_animation.tick()
            self.position = self.glide_animation.getCurrentPosition()
            if self.glide_animation.isFinished():
                self.position = self.glide_animation.end
                self.gliding = False
        
    def render(self, surface):
        surface.blit(self.texture, self.position)
        
    def glide(self, new_position : tuple):
        self.gliding = True
        self.glide_animation = GlideAnimation(self.position, new_position)
        
class SetCard(VisualCard):
    WRONG_BLINK_DURATION = 0.2 # seconds
    WRONG_BLINKS = 3 # times
    
    wrong_blink_ticks = WRONG_BLINK_DURATION * FPS # the amount of ticks the blink is displayed
    wrong_blink_cycle_ticks = 2 * wrong_blink_ticks # the amount of ticks it is displayed AND not displayed
    wrong_blink_total_ticks = wrong_blink_cycle_ticks * WRONG_BLINKS
    
    @classmethod
    def initialize(cls):
        cls.you_selected_texture = ImageLoader.loadImage("overige afbeeldingen\\selection_box.png").copy()
        cls.pc_selected_texture = ImageLoader.loadImage("overige afbeeldingen\\selection_box.png").copy()
        
        ImageLoader.changeImageColour(cls.you_selected_texture, Colours.YOU.value)
        ImageLoader.changeImageColour(cls.pc_selected_texture, Colours.PC.value)
    
    def __init__(self, position_index, card):
        # Get the filename by getting the values as a list, converting those values to strings and joining it together
        filename = "".join([str(x) for x in card.getValues()])
        
        super().__init__(grid.posities[position_index], filename)
        
        self.position_index = position_index
        self.kaart = card
        
        self.selection_handler = SelectionHandler(self)
        self.you_selected = False
        self.pc_selected = False
        
        self.wrong_blink_layer_texture = ImageLoader.loadImage("overige afbeeldingen\\wrong_blink_layer.png")
        self.wrong_blink_tick = -1
        
        self.chosen = False
        
    def tick(self):
        super().tick()
        
        # update wrong blink effect
        if self.wrong_blink_tick >= 0:
            self.wrong_blink_tick += 1
            if self.wrong_blink_tick >= SetCard.wrong_blink_total_ticks:
                self.wrong_blink_tick = -1
                
        # delete card when correctly chosen
        if self.chosen and not self.gliding:
            game_objects.remove(self)
            mouse_listeners.remove(self.selection_handler)
            grid.cards.remove(self)
        
    def render(self, surface):
        # render selection
        if self.you_selected:
            surface.blit(self.you_selected_texture, (self.position[0] - 5, self.position[1] - 5))
            
        if self.pc_selected:
            surface.blit(self.pc_selected_texture, (self.position[0] - 5, self.position[1] - 5))
            
        super().render(surface)
        # render wrong blink effect
        if self.wrong_blink_tick >= 0:
            if self.wrong_blink_tick % SetCard.wrong_blink_cycle_ticks < SetCard.wrong_blink_ticks:
                surface.blit(self.wrong_blink_layer_texture, self.position)
    
    def click(self, position):
        if game_phase == GamePhase.SETS_VINDEN:
            self.you_selected = not self.you_selected
            if self.you_selected:
                selected_cards.append(self)
            else:
                selected_cards.remove(self)
                
            SoundPlayer.playSound("audio\\card_select.wav")
    
    def isMouseInside(self, position):
        bounding_box = pygame.Rect(self.position, (VisualCard.WIDTH, VisualCard.HEIGHT))
        return bounding_box.collidepoint(position)
    
    def __repr__(self):
        return f"SetCard({self.kaart})"
    
class ScoreCard(VisualCard):
    # worden in initialize() aangemaakt:
    SCORE_FONT = None
    NAME_FONT = None
    
    SCORE_FONT_SIZE = 72
    NAME_FONT_SIZE = 36
    
    def __init__(self, position, player):
        super().__init__(position, "blank")
        
        self.player = player
        
        self.z_index = 10
        
    def render(self, surface):
        super().render(surface)
        
        score_text_surface = ScoreCard.SCORE_FONT.render(str(self.player.score), True, self.player.colour)
        score_text_rect = score_text_surface.get_rect()
        
        score_text_center_x = self.position[0] + self.WIDTH // 2
        score_text_center_y = self.position[1] + self.HEIGHT // 3 * 2
        score_text_x = score_text_center_x - score_text_rect.width // 2
        score_text_y = score_text_center_y - score_text_rect.height // 2
        
        surface.blit(score_text_surface, (score_text_x, score_text_y))
        
        name_text_surface = ScoreCard.NAME_FONT.render(self.player.name, True, self.player.colour)
        name_text_rect = name_text_surface.get_rect()
        
        name_text_center_x = self.position[0] + self.WIDTH // 2
        name_text_center_y = self.position[1] + self.HEIGHT // 3
        name_text_x = name_text_center_x - name_text_rect.width // 2
        name_text_y = name_text_center_y - name_text_rect.height // 2
        
        surface.blit(name_text_surface, (name_text_x, name_text_y))

class Menu:
    global SCREEN_WIDTH, SCREEN_HEIGHT
    
    @classmethod
    def initialize(cls):
        #Positie van het menu en de bijbehorende knoppen
        cls.menu_width = VisualCard.HEIGHT + 2 * grid.card_margin
        cls.menu_height = 3 * VisualCard.WIDTH + 4 * grid.card_margin
        cls.positie = ((SCREEN_WIDTH - cls.menu_width) // 2, (SCREEN_HEIGHT - cls.menu_height) // 2)
        cls.easy_position = (cls.positie[0] + grid.card_margin, cls.positie[1] + grid.card_margin)
        cls.normal_position = (cls.positie[0] + grid.card_margin, cls.easy_position[1] + grid.card_margin+VisualCard.WIDTH)
        cls.hard_position = (cls.positie[0] + grid.card_margin, cls.normal_position[1] + grid.card_margin+VisualCard.WIDTH)
    
    def __init__(self, filename = 'menu'):
        self.position = Menu.positie
        self.texture = ImageLoader.loadImage(f"overige afbeeldingen\\{filename}.png")
        
        self.easy = Button(30, self.easy_position, 'easy')
        self.normal = Button(15, self.normal_position, 'normal')
        self.hard = Button(8, self.hard_position, 'hard')
        
        self.z_index = 20
        
        game_objects.append(self)
        
    def render(self, surface):
        if game_phase == GamePhase.MENU:
            surface.blit(self.texture, self.position)
    
    def tick(self):
        pass
        
class Button:
    def __init__(self, seconds_to_choose_set, position = (0,0), filename = 'blank'):
        self.position = position
        self.seconds_to_choose_set = seconds_to_choose_set
        
        self.texture = ImageLoader.loadImage(f"overige afbeeldingen\\{filename}.png")
        
        self.selection_handler = SelectionHandler(self)
        
        self.selected = False
        
        self.z_index = 30
        
        game_objects.append(self)
    
    def render(self, surface):
        if game_phase == GamePhase.MENU:
            surface.blit(self.texture, self.position)
        
    def tick(self):
        pass
    
    def click(self, position):
        global game_phase, total_ticks_since_phase_change, SECONDS_TO_CHOOSE_SET
        if game_phase == GamePhase.MENU:
            SECONDS_TO_CHOOSE_SET = self.seconds_to_choose_set
            reset()
            game_phase = GamePhase.GAME_START
    
    def isMouseInside(self, position):
        bounding_box = pygame.Rect(self.position, (VisualCard.HEIGHT, VisualCard.WIDTH))
        return bounding_box.collidepoint(position)

# === OTHER OBJECTS ===
@dataclass(frozen = True)
class Kaart:
    kleur : int
    vorm : int
    vulling : int
    aantal : int
    
    def getValues(self):
        return [self.kleur, self.vorm, self.vulling, self.aantal]
    
    # Een getal tussen de 0 en 80 die een kaart uniek identificeert
    # Wordt gebruikt bij sorteren en Binary Search
    def getID(self):
        return (self.kleur - 1) * 27 + (self.vorm - 1) * 9 + (self.vulling - 1) * 3 + self.aantal - 1

class Player:
    def __init__(self, name, colour, score_card_position):
        self.name = name
        self.colour = colour
        self.score = 0
        
        self.score_card = ScoreCard(score_card_position, self)
        game_objects.append(self.score_card)

@dataclass
class Layer:
    #Een class om ervoor te zorgen dat afbeeldingen in de juiste volgorde boven elkaar liggen
    z_index : int
    surface : pygame.Surface
    used : bool = True
    
class ImageLoader:
    images = {}
    
    @classmethod
    def loadImage(cls, filename):
        if filename in cls.images:
            return cls.images[filename]
        
        image = pygame.image.load(filename)
        cls.images[filename] = image
        return image
    
    @staticmethod
    def changeImageColour(surface, colour):
        r, g, b = colour
        width, height = surface.get_size()
        for x in range(width):
            for y in range(height):
                alpha = surface.get_at((x, y))[3]
                surface.set_at((x, y), (r, g, b, alpha))

class SoundPlayer:
    sounds = {}
    
    @classmethod
    def playSound(cls, filename):
        if filename in cls.sounds:
            sound = cls.sounds[filename]
        else:
            sound = pygame.mixer.Sound(filename)
            cls.sounds[filename] = sound
            
        pygame.mixer.Sound.play(sound)

@dataclass
class GlideAnimation:
    begin : tuple
    end : tuple
    current_tick : int
    
    GLIDE_DURATION = 0.7 # seconds
    total_glide_ticks = int(GLIDE_DURATION * FPS)
    
    def __init__(self, begin, end, current_tick = 0):
        self.begin = begin
        self.end = end
        self.current_tick = current_tick
        
    def tick(self):
        self.current_tick += 1
        
    def getCurrentPosition(self):
        dx = self.end[0] - self.begin[0]
        dy = self.end[1] - self.begin[1]
        dt = self.current_tick / GlideAnimation.total_glide_ticks
        #Zesdegraads functie die de snelheid van de kaart aanpast over tijd
        f = -0.2*(dt - 1.31) ** 6 + 1
        # f = 2 / (1 + 2 ** (- 11 * dt)) - 1
        
        x = self.begin[0] + dx * f
        y = self.begin[1] + dy * f
        return (x, y)
    
    def isFinished(self):
        return self.current_tick >= GlideAnimation.total_glide_ticks
    
class SelectionHandler:
    def __init__(self, clickable_object):
        mouse_listeners.append(self)
        self.clickable_object = clickable_object
        self.mouse_down_on_object = False
        
    def mouseDown(self, position):
        if self.clickable_object.isMouseInside(position):
            self.mouse_down_on_object = True
    
    def mouseUp(self, position):
        if self.mouse_down_on_object and self.clickable_object.isMouseInside(position):
            self.clickable_object.click(position)
            
        self.mouse_down_on_object = False

class Grid:
    TIJD_TUSSEN_UITDELEN = 0.2 # seconds
    
    ticks_tussen_uitdelen = int(TIJD_TUSSEN_UITDELEN * FPS)
    
    def initializePositions(self):
        #Bepalen van de posities van de kaarten, stapel en aflegstapel aan de hand van de grootte van het scherm en de kaarten
        self.posities = []
        temp_x = (SCREEN_WIDTH - 7 * VisualCard.WIDTH - 6 * self.card_margin) // 2
        temp_y = (SCREEN_HEIGHT - 2 * VisualCard.HEIGHT - self.card_margin) // 2
        for y in range(2):
            for x in range(6):
                self.posities.append((temp_x, temp_y))
                temp_x += VisualCard.WIDTH + self.card_margin
            if y == 1:
                break
            temp_x = (SCREEN_WIDTH - 7 * VisualCard.WIDTH - 6 * self.card_margin) // 2
            temp_y += VisualCard.HEIGHT + self.card_margin
            
        self.trekstapel_positie = (temp_x + VisualCard.WIDTH + self.card_margin, temp_y - (VisualCard.HEIGHT + 2 * self.card_margin))
        self.aflegstapel_positie = (temp_x + VisualCard.WIDTH + self.card_margin, temp_y + self.card_margin)
        
    def __init__(self, card_margin):
        self.card_margin = card_margin
        self.initializePositions()
        
        self.trekstapel = VisualCard(self.trekstapel_positie)
        self.trekstapel.z_index = -10
        game_objects.append(self.trekstapel)
        
        self.aflegstapel = VisualCard(self.aflegstapel_positie, filename = "lege_stapel")
        self.aflegstapel.z_index = -10
        game_objects.append(self.aflegstapel)
        
        self.reset()
        
    def reset(self):
        self.stapel_op = False
        #Het toevoegen van alle kaarten op de stapel
        self.kaarten_op_stapel = []
        for kleur in range(1,4):
            for vorm in range(1,4):
                for vulling in range(1,4):
                    for aantal in range(1,4):
                        self.kaarten_op_stapel.append(Kaart(kleur, vorm, vulling, aantal))
        #Het schudden van de stapel
        random.shuffle(self.kaarten_op_stapel)
        
        self.cards = []
        self.trekstapel.texture = ImageLoader.loadImage("kaarten\\blank.gif")
        self.aflegstapel.texture = ImageLoader.loadImage("kaarten\\lege_stapel.gif")
        self.aflegstapel.z_index = -10

    def plaatsKaart(self, kaart, lege_plek_index):
        #Functie die kaarten naar een lege positie in de Grid beweegt
        card = SetCard(lege_plek_index, kaart)
        card.position = self.trekstapel_positie
        
        game_objects.append(card)
        self.cards.append(card)
        card.glide(self.posities[lege_plek_index])
        
        SoundPlayer.playSound("audio\\card_place.wav")
                
    def getKaarten(self):
        return [card.kaart for card in self.cards]
    
    def deselectAllCards(self):
        global selected_cards
        for card in selected_cards:
            card.you_selected = False
            card.pc_selected = False
        selected_cards = []
        
    def doorschuiven(self):
        lege_plekken = [i for i in range(12)]
        #Lijst van alle SetCards in game_objects
        setCards = []
        for game_object in game_objects:
            if type(game_object) is SetCard:
                setCards.append(game_object)
        #Verwijderen van alle posities in de grid waar een kaart ligt; zo blijven de lege plekken over
        for i in range(12):
            for card in setCards:
                if card.position_index == i:
                    lege_plekken.remove(i)
        #Verplaatsen van kaarten naar lege plekken als nodig
        for card in setCards:
            for i in range(12):
                if i in lege_plekken:
                    if i < card.position_index:
                        card.glide(self.posities[i])
                        lege_plekken.append(card.position_index)
                        card.position_index = i
                        lege_plekken.remove(i)
                
    def nieuweKaart(self):
        #Functie voor het uitdelen van nieuwe kaarten
        lege_plek = self.legePlekken()[0]
        kaart = self.kaarten_op_stapel.pop()
        self.plaatsKaart(kaart, lege_plek)
        if len(self.kaarten_op_stapel) == 0:
            self.stapel_op = True
            self.trekstapel.texture = ImageLoader.loadImage("kaarten\\lege_stapel.gif")
                
    def legePlekken(self):
        lege_plekken = [i for i in range(12)]
        for card in self.cards:
            lege_plekken.remove(card.position_index)
        return lege_plekken
        
# Start het spel
if __name__ == "__main__":
    initialize()