from dataclasses import dataclass
import pygame

@dataclass
class Kaart:
    kleur : int
    vorm : int
    vulling : int
    aantal : int

def main():
    pygame.init()

if __name__ == "__main__":
    main()