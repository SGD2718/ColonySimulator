from power_source import PowerSource


class NuclearReactor(PowerSource):
    YEARS_TO_SECONDS = 365.2425 * 24 * 3600  # 365.2425 is based on skipping leap years

    def __init__(self,
                 **kwargs
                 ):
        """

        this will default to be like the SVBR-10 microreactor
        :keyword fuel_capacity: fuel capacity in kg (default 264 kg),
        :keyword fuel_lifespan: lifespan of one fuel load in years (default 20 yr)
        :keyword: thermal_output: thermal energy output in MWt (default 50 MWt)
        :keyword: electrical_output: thermal energy output in MWe (default 12 MWt)
        """
        super().__init__()
        self.fuel_capacity = kwargs.get('fuel_capacity', 264)
        self.fuel_lifespan = kwargs.get('fuel_lifespan', 20) * NuclearReactor.YEARS_TO_SECONDS
        self.electrical_output = kwargs.get('electrical_output', 12) * 1e6
        self.heat_output = kwargs.get('heat_output', 50) * 1e6
        self.fuel_consumption_rate = self.fuel_capacity / self.fuel_lifespan

        self.fuel = float(self.fuel_capacity)

    def generate(self, dt: float = 0.0333) -> None:
        dt_used = min(self.fuel / self.fuel_consumption_rate, dt)
        self.fuel -= self.fuel_consumption_rate * dt_used

        self.electrical_energy += self.electrical_output * dt_used
        self.thermal_energy += self.thermal_energy * dt_used


