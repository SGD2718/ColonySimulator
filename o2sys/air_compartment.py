from abc import ABC, abstractmethod
from o2sys.pressurizer import *
from air_graph import AirGraph


class AirCompartment:
    def __init__(self, name: str, volume: float):
        self.name = name
        self.volume = volume

        self.o2_density: float = 0
        self.co2_density: float = 0

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return self.name == other

    def get_o2_density(self) -> float:
        return self.o2_density

    def get_co2_density(self) -> float:
        return self.co2_density

    def get_volume(self) -> float:
        return self.volume

    def apply_flux(self, o2_density_flux: float, co2_density_flux: float, dt: float = 0.033) -> None:
        """
        Applies flux changes o2 and co2 density
        :param o2_density_flux: O2 density flux
        :param co2_density_flux: CO2 density flux
        :param dt: time step since last update
        """
        self.o2_density += o2_density_flux * dt
        self.co2_density += co2_density_flux * dt


class Atmosphere(AirCompartment):
    def __init__(self):
        super().__init__("Atmosphere", float('inf'))

    def get_o2_density(self) -> float:
        return 3.2e-5

    def get_co2_density(self) -> float:
        return 0.0191

    def apply_flux(self, o2_density_flux: float, co2_density_flux: float, dt: float = 0.033) -> None:
        pass

