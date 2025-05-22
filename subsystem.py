from abc import ABC, abstractmethod
from power_source import PowerSource


class Subsystem(ABC):

    def __init__(self, name: str, power_source: PowerSource):
        self.name = name
        self.power_source: PowerSource = power_source

    def __repr__(self):
        return self.name

    @abstractmethod
    def update(self, dt: float = 0.0333) -> float:
        """
        Updates the subsystem.
        :param dt: time step between updates
        :return: heat produced by the subsystem
        """
        raise NotImplementedError
