# a collection of connected rooms
from room import *
from door import Door
from nuclear_reactor import *
from o2sys.air_graph import *


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

    def _update_systems(self):
        for room in self.rooms:
            room.update_systems()
