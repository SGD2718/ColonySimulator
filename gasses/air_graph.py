import numpy as np
import chemicals as chem


class AirGraph:

    from air_valve import AirValve
    from air_compartment import AirCompartment

    def __init__(self,
                 name: str,
                 compartments: list[AirCompartment],
                 valves: list[AirValve],
                 temperature: float = 298.15,
                 heat_loss_rate: float = 0.05):
        """

        :param name:
        :param compartments:
        :param valves:
        :param temperature:
        :param heat_loss_rate: proportion of heat loss per second
        """
        self.name = name
        self.compartments = compartments
        self.heat_loss_rate = heat_loss_rate
        self.valves = valves

        self.temperature = temperature

    def _update_temperature(self, heat: float, dt: float = 0.0333, **kwargs) -> None:
        mode = kwargs.get('mode', 'power')

        total_masses = np.add.reduce((c.get_densities() * c.get_volume() for c in self.compartments))
        heat_capacities = np.asarray(
            [
                chem.O2.specific_heat_capacity(self.temperature),
                chem.CO2.specific_heat_capacity(self.temperature),
                chem.N2.specific_heat_capacity(self.temperature),
                chem.H2O.specific_heat_capacity(self.temperature)
            ],
            dtype=float
        )

        # Q = ∑mc∆T => ∆T = Q / ∑mc
        if mode == "power":
            q_in = heat * dt
        else:
            q_in = float(heat)

        self.temperature = (self.temperature * (self.heat_loss_rate ** dt) +
                            q_in / (np.dot(heat_capacities, total_masses)))

    def _update_airflow(self, dt: float = 0.0333) -> None:
        """
        Updates the airflow
        :param dt: change in time
        """
        for valve in self.valves:
            valve.compute_flux(self.temperature)

        for valve in self.valves:
            valve.apply_flux(dt)

    def get_temperature(self) -> float:
        return self.temperature
