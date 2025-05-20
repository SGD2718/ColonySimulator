from room import *
from habitat import *
from o2sys.air_valve import *


class Door(AirValve):
    # the thickness of the gap between an unpressurized door and the door frame in meters
    UNSEALED_PERIMETER_GAP = 0.01

    def __init__(self,
                 name: str,
                 is_airtight: bool,
                 dims: tuple[float | int, float | int],
                 room1: Room | None = None,
                 room2: Room | None = None):
        """
        :param parent: parent habitat
        :param name: door name
        :param is_airtight: whether the door is airtight
        :param dims: (width, height) tuple of the door dimensions in meters
        :param room1: room on one side of the door
        :param room2: room on the other side of the door
        """
        super().__init__(
            name,
            dims[0] * dims[1],
            dims[0] * dims[1] - (dims[0] - Door.UNSEALED_PERIMETER_GAP) * (dims[1] - 2 * Door.UNSEALED_PERIMETER_GAP) if is_airtight else 0,
            room1,
            room2
        )

        self._is_airtight = is_airtight

    def is_airtight(self) -> bool:
        """
        :return: True if the door is airtight, False otherwise
        """
        return self._is_airtight
