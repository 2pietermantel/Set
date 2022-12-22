import pygame
import set

# Some variables
WIDTH = 800
HEIGHT = 600

# Colors
COLOR_BACKGROUND = (221, 221, 221)

game_objects = []

def initialize():
    pygame.init()
    
    game_objects.append(VisualCard(set.Kaart(1,2,3,1), 100, 300))
    
    main()
    
def main():
    # Initialize screen
    FPS = pygame.time.Clock()
    FPS.tick(60)
    
    canvas = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Set!")
    
    running = True
    while running:
        # Check if the game should quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Rendering
        canvas.fill(COLOR_BACKGROUND)
        
        for game_object in game_objects:
            game_object.render(canvas)
        
        pygame.display.update()
                
    pygame.quit()
    
class VisualCard:
    def __init__(self, kaart, x = 0, y = 0):
        self.kaart = kaart
        self.x = x
        self.y = y
        
        # Load texture
        naam = "".join([str(i) for i in kaart.getValues()])
        self.texture = pygame.image.load(f"kaarten\\{naam}.gif")
        
    def render(self, canvas):
        canvas.blit(self.texture, (self.x, self.y))