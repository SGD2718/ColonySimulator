from subsystem import Subsystem
from power_source import PowerSource
import chemicals


class SabatierReactor(Subsystem):
    # https://en.wikipedia.org/wiki/Sabatier_reaction
    # Sabatier Reaction: CO2 + 4H2 -> CH4 + 2H2O, ∆H = −206 kJ/mol
    # 1 kg CH4/day * 1000 mol CH4 / 16.043 kg CH4 * 1 mol Rxn / 1 mol CH4 * 1 day / 86400 s / 700W
    #   = 1.03062965371E-6 mol rxn/J

    # 1.03062965371E-6 mol rxn/J * 16.043 kg CH4 / 1000 mol Rxn = 1.6534391534E-8 kg CH4 / s / W
    # 1.03062965371E-6 mol rxn/J * 2 * 18.01528 kg H2O / 1000 mol Rxn = 3.7134163576E-8 kg H2O / s / W
    # 1.03062965371E-6 mol rxn/J * 4 * 2.016 kg H2 / 1000 mol Rxn = 8.3109975275E-9 kg H2 / s / W
    # 1.03062965371E-6 mol rxn/J * 44.009 kg CO2 / 1000 mol Rxn = 4.535698043E-8 kg CO2 / s / W
    # 1.03062965371E-6 mol rxn/J * −206 kJ/mol = 0.212309708664 J Heat/J

    _BASE_KG_CH4_PER_DAY = 1
    _BASE_EFFICIENCY = 1
    _BASE_POWER = 700

    REACTION_RATE = _BASE_KG_CH4_PER_DAY / 86400 / gasses.CH4.molar_mass_kg_mol / (_BASE_POWER * _BASE_EFFICIENCY)
    CH4_REACTION_RATE = REACTION_RATE * gasses.CH4.molar_mass_kg_mol
    H2O_REACTION_RATE = 2 * REACTION_RATE * gasses.H2O.molar_mass_kg_mol
    H2_REACTION_RATE = 4 * REACTION_RATE * gasses.H2.molar_mass_kg_mol
    CO2_REACTION_RATE = REACTION_RATE * gasses.CO2.molar_mass_kg_mol
    ENTHALPY_RATE = 206000 * REACTION_RATE

    def __init__(self,
                 name: str,
                 power_consumption: float = 700.0,
                 power_source: PowerSource = None,
                 efficiency: float = 1.0,
                 energy_tolerance: float = 0.0):
        """

        :param name: reactor name
        :param power_consumption: power consumption
        :param power_source: power source
        :param efficiency: efficiency
        :param energy_tolerance: maximum energy shortage for operation to occur
        """
        super().__init__(power_source)

        self._efficiency = efficiency
        self.power_consumption = power_consumption
        self.name = name

        self._energy_to_start = 0
        self._co2 = 0
        self._h2 = 0
        self._ch4 = 0
        self._h2o = 0

    def __repr__(self):
        return f'SabatierReactor({self.name})'

    def get_name(self):
        return self.name

    def get_efficiency(self):
        return self._efficiency

    def harvest_water(self, amount) -> float:
        """
        Harvest water from the Sabatier reactor
        :param amount: desired mass of water in kg
        :return: actual amount of water removed in kg
        """
        amount = min(self._h2o, amount)
        self._h2o -= amount
        return amount

    def feed_reactants(self, co2_mass_flux: float, h2_mass_flux: float, dt: float = 0.033) -> None:
        self._h2 += h2_mass_flux * dt
        self._co2 += co2_mass_flux * dt

    def update(self, dt: float = 0.033, co2_mass_flux: float = 0, h2_mass_flux: float = 0) -> float:
        """
        React the Sabatier reactor
        :param co2_mass_flux: influx of CO gas
        :param h2_mass_flux: influx of H2 gas
        :param dt: time step between updates
        :return: heat produced by the subsystem
        """

        #
        self.feed_reactants(co2_mass_flux, h2_mass_flux, dt)
        energy_used = self.power_consumption * dt
        self._energy_to_start = max(self._energy_to_start + energy_used - self.power_source.consume_energy(energy_used),
                                    0)

        heat = energy_used * (1 - self._efficiency)
        energy_used -= heat

        if self._energy_to_start == 0:
            h2_used = SabatierReactor.H2_REACTION_RATE * energy_used
            co2_used = SabatierReactor.CO2_REACTION_RATE * energy_used

            if co2_used < self._co2 and h2_used < self._h2:
                self._h2 -= h2_used
                self._co2 -= co2_used
                self._h2o += SabatierReactor.H2O_REACTION_RATE * energy_used
                self._ch4 += SabatierReactor.CH4_REACTION_RATE * energy_used
                return heat + SabatierReactor.ENTHALPY_RATE * energy_used
            else:
                proportion_reacted = min(h2_used / self._h2, co2_used / self._co2)
                energy_used *= proportion_reacted
                self._h2 -= h2_used * proportion_reacted
                self._co2 -= co2_used * proportion_reacted
                self._h2o += SabatierReactor.H2O_REACTION_RATE * energy_used
                self._ch4 += SabatierReactor.H2O_REACTION_RATE * energy_used
                return heat + SabatierReactor.ENTHALPY_RATE * energy_used

        return heat
