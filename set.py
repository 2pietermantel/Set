import pygame
from dataclasses import dataclass

# === VARIABELEN ===
WIDTH = 1280 # pixels
HEIGHT = 720 # pixels

GLIDE_DURATION = 1 # seconds
FPS = 60

# Colours (R, G, B)
COLOR_BACKGROUND = (221, 221, 221)

# === PROGRAMMEERVARIABELEN ===
CARD_WIDTH = 100
CARD_HEIGHT = 200

game_objects = [] # tick(); render(canvas)
mouse_listeners = [] # mouse_down(position), mouse_up(position)

total_glide_ticks = int(GLIDE_DURATION * FPS)

card_selection_box = pygame.image.load("kaarten\\selection_box.gif")

# === ALLES RONDOM DE LOGICA ACHTER SET ===
@dataclass(frozen = True)
class Kaart:
    kleur : int
    vorm : int
    vulling : int
    aantal : int
    
    def getValues(self):
        return [self.kleur, self.vorm, self.vulling, self.aantal]

# === ALLES RONDOM HET GUI ===
def initialize():
    pygame.init()
    
    vc = SetCard(position = (300, 100), card = Kaart(2,3,3,1))
    
    vc.glide((200, 200))
    game_objects.append(vc)
    
    loop()
    
def loop():
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
                    mouse_listener.mouse_down(pygame.mouse.get_pos())
                    
            if event.type == pygame.MOUSEBUTTONUP:
                for mouse_listener in mouse_listeners:
                    mouse_listener.mouse_up(pygame.mouse.get_pos())
                
        # ticking
        for game_object in game_objects:
            game_object.tick()
        
        # Rendering
        canvas.fill(COLOR_BACKGROUND)
        
        for game_object in game_objects:
            game_object.render(canvas)
        
        pygame.display.update()
        
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

# === OTHER OBJECTS ===
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
        # TODO: Betere animatie
        # self.begin en self.end zijn de begin- en eindcoördinatien als tuple
        # self.current_tick is op welke frame de animatie is
        # total_glide_time is de totale tijd die de animatie moet duren
        # return een tuple met de coördinaten op het huidige moment
        
        # voor nu is het een beweging met constante snelheid, maar het moet iets vloeiender worden
        
        dx = self.end[0] - self.begin[0]
        dy = self.end[1] - self.begin[1]
        dt = self.current_tick / total_glide_ticks
        f = -0.2*(dt-1.5)**4+1
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
        
    def mouse_down(self, position):
        if self.clickable_object.isMouseInside(position):
            self.mouse_down_on_object = True
    
    def mouse_up(self, position):
        if self.mouse_down_on_object and self.clickable_object.isMouseInside(position):
            self.clickable_object.click(position)
            
        self.mouse_down_on_object = False
    
# === FUNCTIES ===    
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

# Start het spel
if __name__ == "__main__":
    initialize()