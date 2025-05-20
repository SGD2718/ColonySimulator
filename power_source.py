from abc import ABC, abstractmethod


class PowerSource(ABC):
    def __init__(self):
        self.energy = 0

    @abstractmethod
    def generate(self, dt: float = 0.0333) -> None:
        """
        generate power
        """
        raise NotImplementedError

    def charge(self, power: float, dt: float = 0.0333) -> None:
        """
        add power
        """
        self.energy += power * dt

    def consume_power(self, power: float, dt: float = 0.0333) -> float:
        """
        consume power.
        :param power: power consumption
        :param dt: change in time
        :return: consumed energy
        """
        delta_energy = min(power * dt, self.energy)
        self.energy -= delta_energy
        return delta_energy

    def consume_energy(self, energy: float) -> float:
        """
        consume power.
        :param energy: energy consumption
        :return: consumed energy
        """
        delta_energy = min(energy, self.energy)
        self.energy -= delta_energy
        return delta_energy


