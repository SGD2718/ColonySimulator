from abc import ABC, abstractmethod
from power_source import PowerSource


class Subsystem(ABC):

    def __init__(self, power_source: PowerSource):
        self.power_source = power_source

    @abstractmethod
    def update(self, dt: float = 0.0333) -> float:
        """
        Updates the subsystem.
        :param dt: time step between updates
        :return: heat produced by the subsystem
        """
        raise NotImplementedError
