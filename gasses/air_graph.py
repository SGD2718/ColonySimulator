import networkx as nx
import math


class AirGraph:

    from air_valve import AirValve
    from air_compartment import AirCompartment

    def __init__(self,
                 name: str,
                 compartments: list[AirCompartment],
                 valves: list[AirValve],
                 temperature: float = 298.15):

        self.name = name
        self.compartments = compartments
        self.valves = valves

        self.temperature = temperature

    def _update_temperature(self, heat):
        total_o2_mass = 0
        total_co2_mass = 0

        for compartments in self.compartments:
            total_o2_mass += compartments.get_o2_density() * compartments.get_volume()
            total_co2_mass += compartments.get_co2_density() * compartments.get_volume()

        # Q = (m1c1 + m2c2)∆T => ∆T = Q / ∑mc
        self.temperature += (heat /
                             (gasses.O2.specific_heat_capacity(self.temperature) * total_o2_mass +
                              gasses.CO2.specific_heat_capacity(self.temperature) + total_co2_mass))


    def _update_airflow(self, dt: float = 0.0333) -> None:
        """
        Updates the airflow
        :param dt: change in time
        """
        for valve in self.valves:
            valve.compute_flux(self.temperature)

        for valve in self.valves:
            valve.apply_flux(dt)
