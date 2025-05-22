import chemicals as chem
import math
import air
import numpy as np


class AirValve:

    from air_compartment import AirCompartment

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

        self._flux = np.zeros((4,), dtype=float)

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
            self._flux = np.zeros((4,), dtype=float)
            return

        two_rt = (2 * temperature) * air.GAS_CONSTANTS
        upstream_densities = np.maximum(self.compartment1.densities, self.compartment2.densities)
        downstream_densities = np.minimum(self.compartment1.densities, self.compartment2.densities)
        upstream_volumes = np.where(self.compartment1.densities > self.compartment2.densities,
                                    self.compartment1.volume, -self.compartment2.volume)

        self._flux = (upstream_densities * cross_sectional_area / upstream_volumes *
                      np.sqrt(two_rt * np.log(downstream_densities / upstream_densities)))

        self._flux *= self.compartment1.filter * self.compartment2.filter

    def apply_flux(self, dt: float = 0.0333) -> None:
        """
        Apply the flux to the adjacent compartments
        :param dt: change in time since last update
        """
        if self._is_open:
            self.compartment1.apply_flux(self._flux, dt)
            self.compartment2.apply_flux(-self._flux, dt)
