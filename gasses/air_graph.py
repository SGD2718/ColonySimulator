from air_valve import *
from air_compartment import *
import networkx as nx
import math


class AirGraph:
    def __init__(self,
                 name: str,
                 compartments: list[AirCompartment],
                 valves: list[AirValve],
                 temperature: float = 298.15):

        self.name = name
        self.compartments = compartments
        self.valves = valves
        self.temperature = temperature

    def _update_airflow(self, dt: float = 0.0333) -> None:
        """
        Updates the airflow
        :param dt: change in time
        """
        for valve in self.valves:
            valve.compute_flux(self.temperature)

        for valve in self.valves:
            valve.apply_flux(dt)

    def set_temperature(self, temperature: float) -> None:
        """
        Sets the temperature of the air graph
        :param temperature: new temperature of the air graph
        """
        self.temperature = temperature