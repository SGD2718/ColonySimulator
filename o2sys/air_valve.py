from air_graph import AirGraph
from air_compartment import AirCompartment
import math


class AirValve:
    O2_GAS_CONSTANT = 259.820619394  # J/kg K
    CO2_GAS_CONSTANT = 188.915903565  # J/kg K

    def __init__(self,
                 name: str,
                 open_area: float,
                 closed_area: float,
                 compartment1: AirCompartment,
                 compartment2: AirCompartment):
        """
        :param name: door name
        :param open_area: area when open
        :param closed_area: area when closed
        :param compartment1: room on one side of the door
        :param compartment2: room on the other side of the door
        """
        self._name = name
        self._open_area = open_area
        self._closed_area = closed_area
        self._is_open = False

        self._o2_flux: float = 0
        self._co2_flux: float = 0

        self.compartment1 = compartment1
        self.compartment2 = compartment2

    def __bool__(self) -> bool:
        return self._is_open

    def open(self) -> None:
        """
        Open the valve
        """
        self._is_open = True

    def close(self) -> None:
        """
        Close the valve
        """
        self._is_open = False

    def set_state(self, state: bool) -> None:
        """
        Set the valve state
        :param state: True for open, False for closed
        """
        self._is_open = state

    def is_open(self) -> bool:
        """
        Checks if the valve is open
        :return: True if the valve is open, False otherwise
        """
        return self._is_open

    def get_area(self) -> float:
        return self._open_area if self._is_open else self._closed_area

    def get_name(self) -> str:
        return self._name

    def get_open_area(self) -> float:
        return self._open_area

    def get_closed_area(self) -> float:
        return self._closed_area

    def compute_flux(self, temperature: float) -> None:
        """
        Compute the valve flux
        :param temperature: Temperature in Kelvin
        """
        cross_sectional_area = self.get_area()
        if cross_sectional_area == 0:
            self._o2_flux = 0
            self._co2_flux = 0
            return

        two_rt_o2 = 2 * AirValve.O2_GAS_CONSTANT * temperature
        two_rt_co2 = 2 * AirValve.CO2_GAS_CONSTANT * temperature

        def density_flux(rho1, rho2, two_rt, area, volume):
            return rho1 * area / volume * math.sqrt(two_rt * math.log(rho2 / rho1))

        if self.compartment1.get_o2_density() > self.compartment2.get_o2_density():
            self._o2_flux = density_flux(
                self.compartment1.get_o2_density(),
                self.compartment2.get_o2_density(),
                two_rt_o2,
                self.get_area(),
                self.compartment1.get_volume())
        else:
            self._o2_flux = -density_flux(
                self.compartment2.get_o2_density(),
                self.compartment1.get_o2_density(),
                two_rt_o2,
                self.get_area(),
                self.compartment2.get_volume())

        if self.compartment1.get_co2_density() > self.compartment2.get_co2_density():
            self._co2_flux = density_flux(
                self.compartment1.get_co2_density(),
                self.compartment2.get_co2_density(),
                two_rt_co2,
                cross_sectional_area,
                self.compartment1.get_volume())
        else:
            self._co2_flux = -density_flux(
                self.compartment2.get_co2_density(),
                self.compartment1.get_co2_density(),
                two_rt_co2,
                cross_sectional_area,
                self.compartment2.get_volume())

    def apply_flux(self, dt: float = 0.0333) -> None:
        """
        Apply the flux to the adjacent compartments
        :param dt: change in time since last update
        """
        if self._is_open:
            self.compartment1.apply_flux(self._o2_flux, self._co2_flux, dt)
            self.compartment2.apply_flux(-self._o2_flux, -self._co2_flux, dt)
