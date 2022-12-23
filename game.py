import pygame
import set
from dataclasses import dataclass

# Some variables
WIDTH = 800 # pixels
HEIGHT = 600 # pixels

GLIDE_DURATION = 0.5 # seconds
FPS = 60

# Colors (R, G, B)
COLOR_BACKGROUND = (221, 221, 221)

game_objects = []
total_glide_ticks = GLIDE_DURATION * FPS

def initialize():
    pygame.init()
    
    vc = VisualCard(set.Kaart(1,2,3,1), (100, 300))
    vc.glide((200, 200))
    game_objects.append(vc)
    
    
    main()
    
def main():
    # Initialize screen
    clock = pygame.time.Clock()
    canvas = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Set!")
    
    running = True
    while running:
        # Check if the game should quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
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
    
class VisualCard:
    def __init__(self, kaart, position = (0, 0)):
        self.kaart = kaart
        self.position = position
        self.gliding = False
        
        # Load texture
        naam = "".join([str(i) for i in kaart.getValues()])
        self.texture = pygame.image.load(f"kaarten\\{naam}.gif")
        
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
        x = self.begin[0] + dx * dt
        y = self.begin[1] + dy * dt
        return (x, y)
    
    def isFinished(self):
        return self.current_tick >= total_glide_ticks