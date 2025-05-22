from subsystem import Subsystem
from power_source import PowerSource


class Light(Subsystem):
    # PHOTOSYNTHETIC PHOTON FLUX DENSITY (umol/m^2/s)
    POTATO_PPFD = 700
    QUINOA_PPFD = 600
    BEANS_PPFD = 600
    SPINACH_PPFD = 400
    KALE_PPFD = 400
    BLACKBERRIES_PPFD = 700
    STRAWBERRIES_PPFD = 600

    # DAILY LIGHT INTEGRAL (mol/m^2/day)
    POTATO_DLI = 20
    QUINOA_DLI = 18
    BEANS_DLI = 16
    SPINACH_DLI = 14
    KALE_DLI = 14
    BLACKBERRIES_DLI = 20
    STRAWBERRIES_DLI = 16

    # LED POWER REQUIREMENTS (W/m^2)
    POTATO_POWER = 300
    QUINOA_POWER = 250
    BEANS_POWER = 250
    SPINACH_POWER = 200
    KALE_POWER = 200
    BLACKBERRIES_POWER = 350
    STRAWBERRIES_POWER = 300

    _BASE_EFFICIENCY = 1
    _BASE_BRIGHTNESS = 500
    def __init__(self,
                 name: str,
                 source: PowerSource,
                 dims: tuple[float, float, float],
                 power_per_area_per_lumen,
                 brightness: int = 500,
                 efficiency: float = 1.0):
        """
        :param name: reactor name
        :param source: power source
        :param dims: (width, height, length) tuple of the light source dimensions in meters
        :param power_per_area_per_lumen: needed power to produce light over an area
        :param brightness: brightness level
        :param efficiency: efficiency level
        """
        super().__init__(name, source)
        self.brightness = brightness
        self.name = name
        self._efficiency = efficiency
        self._power = dims[0] * dims[1] * power_per_area_per_lumen * brightness

    def __repr__(self):
        return f'Light({self.name})'

    def get_name(self):
        return self.name

    def get_efficiency(self):
        return self._efficiency

    def update(self, dt: float = 0.0333) -> float:
        """
        Update the light system
        :param dt: time step between updates
        :return: heat produced by the subsystem
        """
        energy_used = self.power_source.consume_energy(self._power * dt)
        heat = self._power * dt
        energy_used -= heat
        return heat
