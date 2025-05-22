from subsystem import Subsystem
from power_source import PowerSource


class Light(Subsystem):
    def __init__(self,
                 name: str,
                 source: PowerSource,
                 dims: tuple[float, float, float],
                 brightness,
                 power_per_area_per_lumen,
                 ):
        super().__init__(name, source)
        self.brightness = brightness


    def update(self, dt: float = 0.0333) -> float:
        used_energy = self.power_source.consume_electricity(power * dt)
        pass
