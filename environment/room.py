from person import *
from light import *
from abc import ABC, abstractmethod, abstractproperty


class Room(ABC):
    def __init__(self, name, volume):
        self.name = name

        self.people: list[Person] = []
        self.lights: list[Light] = []

        self.volume = volume

        self.o2: float = 0
        self.co2: float = 0
        