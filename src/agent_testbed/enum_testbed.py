# set up enum with following values: cat, dog, bird, fish

from enum import Enum


class PuzzleState(Enum):
    cat = 1
    dog = 2
    bird = 3
    fish = 4


# define a variable with the value of the enum
animal = PuzzleState.cat
animal2 = PuzzleState.dog
animal3 = PuzzleState.cat

print(f"Animal: {animal}")
print(f"Animal2: {animal2}")


print(animal == animal2)
print(animal == animal3)
