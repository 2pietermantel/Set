from dataclasses import dataclass
import game

@dataclass
class Kaart:
    kleur : int
    vorm : int
    vulling : int
    aantal : int
    
    def getValues(self):
        return [self.kleur, self.vorm, self.vulling, self.aantal]

def main():
    game.initialize()

if __name__ == "__main__":
    main()