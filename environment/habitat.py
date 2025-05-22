# a collection of connected rooms
from room import Room
from door import Door
from nuclear_reactor import *
from gasses.air_graph import *


class Habitat(AirGraph):
    def __init__(self,
                 name: str,
                 rooms: list[Room],
                 doors: list[Door],
                 reactor: NuclearReactor):

        super().__init__(name, rooms, doors)

        self.name = name
        self.rooms = rooms
        self.reactor = reactor

        self.doors = doors
        self.insulation_efficiency = 0

    def _update_systems(self, dt: float = 0.0333):
        heat = 0
        for room in self.rooms:
            heat += room.update_systems(dt)

        self._update_temperature(heat, dt, mode="energy")

