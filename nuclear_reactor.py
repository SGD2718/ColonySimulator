from power_source import PowerSource


class NuclearReactor(PowerSource):
    def __init__(self):
        super().__init__()
        self.fuel = 100
        self.fuel_consumption = 1
        self.electrical_output = 0
        self.heat_output = 0

        self.heat_tolerance = 0

    def generate(self, dt: float = 0.0333) -> None:
        if self.fuel >= 0:
            self.electrical_energy += self.electrical_output * dt

    def get_electrical_power(self):
        return self.electrical_output

    def get_heat_power(self):
        return self.heat_output

