import numpy as np

from gasses import air
from gasses.sabatier_reactor import SabatierReactor
from power_source import PowerSource
from airtank import AirTank
import chemicals as chem
from subsystem import Subsystem


class Electrolyzer(Subsystem):
    # https://pmc.ncbi.nlm.nih.gov/articles/PMC8426268/
    # https://www.desmos.com/calculator/vly6o2cbbq
    EFFICIENCY = 0.796644641058
    ENTHALPY = 285800 / chem.H2O.molar_mass_kg_mol  # J / mol / (kg / mol)

    @staticmethod
    def _get_h2_mass_output(h2o_mass_input: float) -> float:
        return 0.111332 * h2o_mass_input - 0.181036

    @staticmethod
    def _get_o2_mass_output(h2o_mass_input: float) -> float:
        return 0.888099 * h2o_mass_input

    @staticmethod
    def _get_power_draw(h2o_mass_input: float) -> float:
        """
        Calculate the power required to produce some mass of h2o in 1 second
        :param h2o_mass_input:
        :return:
        """
        return 15712784.6072 * h2o_mass_input + 156606746.559

    @staticmethod
    def _get_h2o_mass_processed(energy_input: float) -> float:
        return max(6.0472588958E-8 * energy_input - 0.00000246343080062, 0)

    def __init__(self,
                 name: str,
                 source: PowerSource,
                 o2_output_tank: AirTank,
                 sabatier_reactor_output: SabatierReactor):
        super().__init__(name, source)

        self.o2_output_tank = o2_output_tank
        self.sabatier_reactor_output = sabatier_reactor_output

        self.h2o_mass_idle = 0
        self.power_draw = 0

        self.h2_mass_released = 0
        self.o2_mass_released = 0

    def update(self, dt: float = 0.0333) -> float:
        energy_used = self.power_source.consume_electricity(self.power_draw, dt)
        h2o_used = Electrolyzer._get_h2o_mass_processed(energy_used)
        self.h2_mass_released += Electrolyzer._get_h2_mass_output(h2o_used)
        self.o2_mass_released += Electrolyzer._get_o2_mass_output(h2o_used)
        self.h2o_mass_idle -= h2o_used

        heat = (1 - Electrolyzer.EFFICIENCY) * energy_used - h2o_used * Electrolyzer.ENTHALPY

        if self.o2_output_tank is not None:
            self.o2_mass_released -= self.o2_output_tank.fill_to_capacity(np.asarray([self.o2_mass_released, 0, 0, 0], dtype=float))
        if self.sabatier_reactor_output is not None:
            self.sabatier_reactor_output.feed_reactants(0, self.h2_mass_released, mode="amount")
            self.h2_mass_released = 0

        return heat

    def collect(self, o2_amount: float, h2_amount: float, dt: float = 0.0333, **kwargs) -> tuple[float, float]:
        mode = kwargs.get('mode', 'flux')

        if mode == "flux":
            collected_o2 = o2_amount * dt
            collected_h2 = h2_amount * dt
        else:
            collected_o2 = o2_amount
            collected_h2 = h2_amount

        self.o2_mass_released -= collected_o2
        self.h2_mass_released -= collected_h2

        return collected_o2, collected_h2

    def add_water(self, h2o_amount: float, dt: float = 0.0333, **kwargs) -> None:
        mode = kwargs.get('mode', 'flux')
        if mode == "flux":
            self.h2o_mass_idle += h2o_amount * dt
        else:
            self.h2o_mass_idle += h2o_amount




