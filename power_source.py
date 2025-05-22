from abc import ABC, abstractmethod


class PowerSource(ABC):
    def __init__(self):
        self.electrical_energy = 0
        self.thermal_energy = 0

    @abstractmethod
    def generate(self, dt: float = 0.0333) -> None:
        """
        generate power
        """
        raise NotImplementedError

    def charge(self, power: float, dt: float = 0.0333) -> None:
        """
        add electrical power
        """
        self.electrical_energy += power * dt

    def heat(self, power: float, dt: float = 0.0333) -> None:
        """
        add thermal power
        """
        self.thermal_energy += power * dt

    def consume_electricity(self, draw: float, dt: float = 0.0333, **kwargs) -> float:
        """
        consume power.
        :param draw: power/energy consumption
        :param dt: change in time
        :param mode: "power" for power, "energy" for energy
        :return: consumed energy
        """
        mode = kwargs.get('mode', 'power')
        if mode == "power":
            delta_energy = min(draw * dt, self.electrical_energy)
        else:
            delta_energy = max(draw, self.electrical_energy)

        self.electrical_energy -= delta_energy
        return delta_energy

    def consume_heat(self, draw: float, dt: float = 0.0333, **kwargs) -> float:
        """
        consume heat power.
        :param draw: power consumption
        :param dt: change in time
        :param mode: "power" for power, "energy" for energy
        :return: consumed energy
        """

        mode = kwargs.get('mode', 'power')
        if mode == "power":
            delta_energy = min(draw * dt, self.thermal_energy)
        else:
            delta_energy = min(draw, self.thermal_energy)
        self.thermal_energy -= delta_energy
        return delta_energy



