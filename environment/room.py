from abc import ABC, abstractmethod


from person import *
from light import *
from door import *
from gasses.pressurizer import *
from gasses.air_compartment import *


class Room(AirCompartment):
    def __init__(self,
                 name: str,
                 dims: tuple[float | int, float | int, float | int],
                 pressurizer: Pressurizer | None = None,
                 lights: list[Light] = None,
                 doors: list[Door] = None):
        super().__init__(
            name,
            dims[0] * dims[1] * dims[2]
        )

        self.people: list[Person] = []
        self.lights: list[Light] = lights
        self.doors: list[Door] = doors

        self.pressurizer = pressurizer

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    def update_systems(self) -> None:
        """
        update all systems in the room
        """
        pass


