import pygame
import random
from dataclasses import dataclass
from enum import Enum

# === VARIABELEN ===
SCREEN_WIDTH = 1280 # pixels
SCREEN_HEIGHT = 720 # pixels

FPS = 60

SECONDS_TO_CHOOSE_SET = 30
# === Enums ===
class GamePhase(Enum):
    GAME_START = 0
    FINDING_SETS = 1
    
class Colours(Enum):
    # (R, G, B) of (R, G, B, A)
    BACKGROUND = (221, 221, 221),
    TRANSPARENT = (0, 0, 0, 0),
    
    PLAYER = (255, 0, 0),
    AI = (0, 255, 0)

# === PROGRAMMEERVARIABELEN ===
# game_objects zijn de objects met de functies tick() en render(surface).
# Ook kunnen ze een int z_index hebben.
game_objects = []

# Objects met een mouseDown(position) en mouseUp(position).
mouse_listeners = []

selected_cards = []

layers = []

total_ticks = 0
total_ticks_since_phase_change = 0
game_phase = GamePhase.GAME_START
total_ticks_since_new_card = 0

# === ALLES RONDOM DE LOGICA ACHTER SET ===
@dataclass(frozen = True)
class Kaart:
    kleur : int
    vorm : int
    vulling : int
    aantal : int
    
    def getValues(self):
        return [self.kleur, self.vorm, self.vulling, self.aantal]
    
def isEenSet(kaarten):
    kaart1 = kaarten[0]
    kaart2 = kaarten[1]
    kaart3 = kaarten[2]
    #Controleren van gelijke kleur
    if kaart1.kleur == kaart2.kleur:
        if kaart1.kleur != kaart3.kleur:
            return False
    else:
        if kaart1.kleur == kaart3.kleur or kaart2.kleur == kaart3.kleur:
            return False
    #Controleren van gelijke vorm
    if kaart1.vorm == kaart2.vorm:
        if kaart1.vorm != kaart3.vorm:
            return False
    else:
        if kaart1.vorm == kaart3.vorm or kaart2.vorm == kaart3.vorm:
            return False
    #Controleren van gelijke vulling
    if kaart1.vulling == kaart2.vulling:
        if kaart1.vulling != kaart3.vulling:
            return False
    else:
        if kaart1.vulling == kaart3.vulling or kaart2.vulling == kaart3.vulling:
            return False
    #Controleren van gelijk aantal
    if kaart1.aantal == kaart2.aantal:
        if kaart1.aantal != kaart3.aantal:
            return False
    else:
        if kaart1.aantal == kaart3.aantal or kaart2.aantal == kaart3.aantal:
            return False
    return True

def vindSets(kaarten):
    combinaties = []
    for index1, kaart1 in enumerate(kaarten[:-2]):
        for index2, kaart2 in enumerate(kaarten[index1+1:-1]):
            for index3, kaart3 in enumerate(kaarten[index2+1:]):
                x = isEenSet([kaart1,kaart2,kaart3])
                if x == True:
                    combinaties.append([kaart1,kaart2,kaart3])
    return combinaties

def vind1Set(kaarten):
    combinaties = vindSets(kaarten)
    if combinaties == []:
        return False
    return combinaties[0]

# === ALLES RONDOM HET GUI ===
def initialize():
    global grid
    pygame.init()
    
    pygame.font.init()
    ScoreCard.FONT = pygame.font.SysFont("Arial", ScoreCard.FONT_SIZE, bold = True)
    
    sc = ScoreCard((20, 20), Colours.PLAYER.value, "JIJ")
    game_objects.append(sc)
    
    grid = Grid(20)
    
    loop()
    
def loop():
    global total_ticks, total_ticks_since_phase_change, total_ticks_since_new_card
    
    # Initialize screen
    clock = pygame.time.Clock()
    canvas = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Set!")
    
    current_game_phase = game_phase
    running = True
    while running:
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
                
        tick()
        
        # Rendering
        canvas.fill(Colours.BACKGROUND.value)
        
        render(canvas)
        
        pygame.display.update()
        
        total_ticks += 1
        if game_phase == GamePhase.FINDING_SETS:
            total_ticks_since_new_card += 1
            
        total_ticks_since_phase_change += 1
        
        if game_phase != current_game_phase:
            total_ticks_since_phase_change = 0
            current_game_phase = game_phase
        
        clock.tick(FPS)
                
    pygame.quit()
    
def tick():
    global selected_cards
    for game_object in game_objects:
        game_object.tick()
        
    grid.tick()
    
    if game_phase == GamePhase.FINDING_SETS:
        if len(selected_cards) == 3:
            kaarten = [card.kaart for card in selected_cards]
            if isEenSet(kaarten):
                pass
            else:
                for card in selected_cards:
                    card.wrong_blink_tick = 0
                    card.selected = False
                selected_cards = []
    
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
    
    def __init__(self, position = (0, 0), card = Kaart(1, 1, 1, 1)):
        # Get the filename by getting the values as a list, converting those values to strings and joining it together
        filename = "".join([str(x) for x in card.getValues()])
        
        super().__init__(position, filename)
        
        self.kaart = card
        
        self.selection_handler = SelectionHandler(self)
        self.selected = False
        self.selection_box_texture = ImageLoader.loadImage("kaarten\\selection_box.png")
        
        self.wrong_blink_layer_texture = ImageLoader.loadImage("kaarten\\wrong_blink_layer.png")
        self.wrong_blink_tick = -1
        
    def tick(self):
        super().tick()
        
        # update wrong blink effect
        if self.wrong_blink_tick >= 0:
            self.wrong_blink_tick += 1
            if self.wrong_blink_tick >= SetCard.wrong_blink_total_ticks:
                self.wrong_blink_tick = -1
        
    def render(self, surface):
        # render selection
        if self.selected:
            surface.blit(self.selection_box_texture, (self.position[0] - 5, self.position[1] - 5))
            
        super().render(surface)
        # render wrong blink effect
        if self.wrong_blink_tick >= 0:
            if self.wrong_blink_tick % SetCard.wrong_blink_cycle_ticks < SetCard.wrong_blink_ticks:
                surface.blit(self.wrong_blink_layer_texture, self.position)
    
    def click(self, position):
        if game_phase == GamePhase.FINDING_SETS:
            self.selected = not self.selected
            if self.selected:
                selected_cards.append(self)
            else:
                selected_cards.remove(self)
            print(selected_cards)
    
    def isMouseInside(self, position):
        bounding_box = pygame.Rect(self.position, (VisualCard.WIDTH, VisualCard.HEIGHT))
        return bounding_box.collidepoint(position)
    
    def __repr__(self):
        return f"SetCard({self.kaart})"
    
class ScoreCard(VisualCard):
    FONT = None # wordt in de initialize() geinitializeerd
    FONT_SIZE = 72
    
    def __init__(self, position, colour, name):
        super().__init__(position, "blank")
        
        self.colour = colour
        self.name = name
        
    def render(self, surface):
        super().render(surface)
        
        score_text_surface = ScoreCard.FONT.render("32", True, self.colour)
        score_text_rect = score_text_surface.get_rect()
        
        score_text_center_x = self.position[0] + VisualCard.WIDTH // 2
        score_text_center_y = self.position[1] + VisualCard.HEIGHT // 3 * 2
        score_text_x = score_text_center_x - score_text_rect.width // 2
        score_text_y = score_text_center_y - score_text_rect.height // 2
        
        surface.blit(score_text_surface, (score_text_x, score_text_y))

# === OTHER OBJECTS ===
@dataclass
class Layer:
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
    
    GLIDE_DURATION = 0.5 # seconds
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
        
        # f = -0.2*(dt-1.5)**4+1
        f = 2 / (1 + 2 ** (- 8 * dt)) - 1
        
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
    def initializePositions(self):
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
        
        self.kaarten_op_stapel = []
        for kleur in range(1,4):
            for vorm in range(1,4):
                for vulling in range(1,4):
                    for aantal in range(1,4):
                        self.kaarten_op_stapel.append(Kaart(kleur, vorm, vulling, aantal))
        
        random.shuffle(self.kaarten_op_stapel)
        
        self.starting_card_placement = 0
        
        self.trekstapel = VisualCard(self.trekstapel_positie)
        self.trekstapel.z_index = -10
        game_objects.append(self.trekstapel)
        
        self.aflegstapel = VisualCard(self.aflegstapel_positie, filename = "lege_aflegstapel")
        game_objects.append(self.aflegstapel)

    def plaatsKaart(self, kaart, lege_plek):
        card = SetCard(self.trekstapel_positie, kaart)
        game_objects.append(card)
        card.glide(self.posities[lege_plek])
        
    def tick(self):
        global game_phase, total_ticks_since_phase_change, total_ticks_since_new_card
        
        if game_phase == GamePhase.GAME_START:
            # check if game start is finished
            if total_ticks_since_phase_change >= 120:
                game_phase = GamePhase.FINDING_SETS
                
        if game_phase == GamePhase.GAME_START:
            # add card
            if total_ticks_since_phase_change % 10 == 0:
                kaart = self.kaarten_op_stapel.pop()
                self.plaatsKaart(kaart, self.starting_card_placement)
                self.starting_card_placement += 1

# Start het spel
if __name__ == "__main__":
    initialize()