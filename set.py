import pygame
import random
from dataclasses import dataclass
from enum import Enum

# === VARIABELEN ===
WIDTH = 1280 # pixels
HEIGHT = 720 # pixels
CARD_MARGIN = 20 # pixels

GLIDE_DURATION = 0.5 # seconds
FPS = 60

# Colours (R, G, B)
COLOR_BACKGROUND = (221, 221, 221)
COLOR_TEXT = (0,0,0)

# === PROGRAMMEERVARIABELEN ===
CARD_WIDTH = 100
CARD_HEIGHT = 200

posities = []
stapel_positie = [0,0]
aflegstapel_positie = [0,0]

game_objects = [] # tick(); render(canvas); int layer 
mouse_listeners = [] # mouseDown(position), mouseUp(position)

total_glide_ticks = int(GLIDE_DURATION * FPS)

card_selection_box = pygame.image.load("kaarten\\selection_box.png")

class GamePhase(Enum):
    game_start = 0
    finding_sets = 1

total_ticks = 0
total_ticks_since_phase_change = 0
game_phase = GamePhase.game_start

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
    
    Grid.initialize()
    
    sc = ScoreCard((20, 20))
    game_objects.append(sc)
    
    grid = Grid()
    
    loop()
    
def loop():
    global total_ticks, total_ticks_since_phase_change
    
    # Initialize screen
    clock = pygame.time.Clock()
    canvas = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Set!")
    
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
                
        # ticking
        grid.tick()
        
        for game_object in game_objects:
            game_object.tick()
        
        # Rendering
        canvas.fill(COLOR_BACKGROUND)
        
        layers = []
        for game_object in game_objects:
            if hasattr(game_object, "z_index"):
                z_index = game_object.z_index
            else:
                z_index = 0
            
            layer = None
            for potential_layer in layers:
                if potential_layer.z_index == z_index:
                    layer = potential_layer
                    
            if layer is None:
                layer = Layer(z_index, pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32))
                layers.append(layer)
                
            game_object.render(layer.surface)
        
        layers.sort(key = lambda layer: layer.z_index)
        for layer in layers:
            canvas.blit(layer.surface, (0, 0))
        
        pygame.display.update()
        
        total_ticks += 1
        total_ticks_since_phase_change += 1
        
        clock.tick(FPS)
                
    pygame.quit()

# === GAME OBJECTS ===
class VisualCard:
    def __init__(self, position = (0, 0), filename = "blank"):
        self.position = position
        self.gliding = False
            
        self.texture = pygame.image.load(f"kaarten\\{filename}.gif")
        
    def tick(self):
        # Handle Glide Animation
        if self.gliding:
            self.glide_animation.tick()
            self.position = self.glide_animation.getCurrentPosition()
            if self.glide_animation.isFinished():
                self.gliding = False
        
    def render(self, canvas):
        canvas.blit(self.texture, self.position)
        
    def glide(self, new_position : tuple):
        self.gliding = True
        self.glide_animation = GlideAnimation(self.position, new_position)
        
class SetCard(VisualCard):
    def __init__(self, position = (0, 0), card = Kaart(1, 1, 1, 1)):
        # Get the filename by getting the values as a list, converting those values to strings and joining it together
        filename = "".join([str(x) for x in card.getValues()])
        
        super().__init__(position, filename)
        
        self.selection_handler = SelectionHandler(self)
        self.selected = False
        
    def render(self, canvas):
        if self.selected:
            canvas.blit(card_selection_box, (self.position[0] - 5, self.position[1] - 5))
        super().render(canvas)
    
    def click(self, position):
        self.selected = not self.selected
    
    def isMouseInside(self, position):
        bounding_box = pygame.Rect(self.position, (CARD_WIDTH, CARD_HEIGHT))
        return bounding_box.collidepoint(position)
    
class ScoreCard(VisualCard):
    FONT = None # wordt in de initialize() geinitializeerd
    FONT_SIZE = 72
    
    def __init__(self, position):
        super().__init__(position, "blank")
        
    def render(self, canvas):
        super().render(canvas)
        
        text_surface = ScoreCard.FONT.render("32", True, COLOR_TEXT)
        rect = text_surface.get_rect()
        
        center_x = self.position[0] + CARD_WIDTH // 2
        center_y = self.position[1] + CARD_HEIGHT // 2
        text_x = center_x - rect.width // 2
        text_y = center_y - rect.height // 2
        
        canvas.blit(text_surface, (text_x, text_y))

# === OTHER OBJECTS ===
@dataclass
class Layer:
    z_index : int
    surface : pygame.Surface

@dataclass
class GlideAnimation:
    begin : tuple
    end : tuple
    current_tick : int
    
    def __init__(self, begin, end, current_tick = 0):
        self.begin = begin
        self.end = end
        self.current_tick = current_tick
        
    def tick(self):
        self.current_tick += 1
        
    def getCurrentPosition(self):
        dx = self.end[0] - self.begin[0]
        dy = self.end[1] - self.begin[1]
        dt = self.current_tick / total_glide_ticks
        
        # f = -0.2*(dt-1.5)**4+1
        f = 2 / (1 + 2 ** (- 8 * dt)) - 1
        
        x = self.begin[0] + dx * f
        y = self.begin[1] + dy * f
        return (x, y)
    
    def isFinished(self):
        return self.current_tick >= total_glide_ticks
    
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
    @classmethod
    def initialize(cls):
        temp_x = (WIDTH - 7 * CARD_WIDTH - 6 * CARD_MARGIN) // 2
        temp_y = (HEIGHT - 2 * CARD_HEIGHT - CARD_MARGIN) // 2
        for y in range(2):
            for x in range(6):
                posities.append((temp_x, temp_y))
                temp_x += CARD_WIDTH + CARD_MARGIN
            if y == 1:
                break
            temp_x = (WIDTH - 7 * CARD_WIDTH - 6 * CARD_MARGIN) // 2
            temp_y += CARD_HEIGHT + CARD_MARGIN
            
        stapel_positie[0] = temp_x + CARD_WIDTH + CARD_MARGIN
        stapel_positie[1] = temp_y - (CARD_HEIGHT +2 * CARD_MARGIN)
        aflegstapel_positie[0] = temp_x + CARD_WIDTH + CARD_MARGIN
        aflegstapel_positie[1] = temp_y + CARD_MARGIN
    
    def __init__(self):
        self.kaarten_op_stapel = []
        for kleur in range(1,4):
            for vorm in range(1,4):
                for vulling in range(1,4):
                    for aantal in range(1,4):
                        self.kaarten_op_stapel.append(Kaart(kleur, vorm, vulling, aantal))
        
        random.shuffle(self.kaarten_op_stapel)
        
        self.starting_card_placement = 0
        
        self.trekstapel = VisualCard(stapel_positie)
        game_objects.append(self.trekstapel)

    def plaatsKaart(self, kaart, lege_plek):
        card = SetCard(stapel_positie, kaart)
        game_objects.append(card)
        card.glide(posities[lege_plek])
        
    def tick(self):
        global game_phase, total_ticks_since_phase_change
        
        if game_phase == GamePhase.game_start:
            # check if game start is finished
            if total_ticks_since_phase_change >= 120:
                game_phase = GamePhase.finding_sets
                total_ticks_since_phase_change = 0
                
        if game_phase == GamePhase.game_start:
            # add card
            if total_ticks_since_phase_change % 10 == 0:
                kaart = self.kaarten_op_stapel.pop()
                self.plaatsKaart(kaart, self.starting_card_placement)
                self.starting_card_placement += 1

# Start het spel
if __name__ == "__main__":
    initialize()