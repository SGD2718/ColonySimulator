from door import Door
from gasses.air_compartment import *
from subsystem import Subsystem


class Room(AirCompartment):
    from habitat import Habitat

    def __init__(self,
                 parent: Habitat,
                 name: str,
                 dims: tuple[float | int, float | int, float | int],
                 systems: list[Subsystem] = None,
                 doors: list[Door] = None):
        super().__init__(
            parent,
            name,
            dims[0] * dims[1] * dims[2]
        )

        self.systems: list[Subsystem] = systems
        self.doors: list[Door] = doors

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def update_systems(self, dt: float = 0.0333) -> float:
        """
        update all systems in the room
        """
        heat = 0
        for system in self.systems:
            heat += system.update(dt)

        return heat



