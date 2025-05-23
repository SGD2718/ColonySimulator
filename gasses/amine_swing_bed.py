import numpy as np
from subsystem import Subsystem  # User provided
from power_source import PowerSource  # User provided
from air_compartment import AirCompartment  # User provided
import air  # User provided
import chemicals as chem  # User provided
import math


class AmineSwingBed(Subsystem):
    """
    Models an amine swing bed system for CO2 and H2O capture.
    The system cycles through adsorption, desorption, and cooling phases.
    """

    # --- Class Constants (Static Variables) ---
    R_UNIVERSAL_GAS_CONSTANT = 8.314462618  # J/(mol·K)
    CO2_MOLAR_MASS_KG_MOL = chem.CO2.molar_mass_kg_mol if hasattr(chem, 'CO2') and hasattr(chem.CO2,
                                                                                           'molar_mass_kg_mol') else 0.04401
    H2O_MOLAR_MASS_KG_MOL = chem.H2O.molar_mass_kg_mol if hasattr(chem, 'H2O') and hasattr(chem.H2O,
                                                                                           'molar_mass_kg_mol') else 0.018015

    DEFAULT_AMINE_MOLAR_MASS_KG_MOL = 0.06108
    DEFAULT_AMINE_SOLUTION_DENSITY_KG_M3 = 1015.0
    DEFAULT_AMINE_SOLUTION_SPECIFIC_HEAT_J_KG_K = 3700.0
    DEFAULT_HEAT_OF_CO2_ABSORPTION_J_MOL = -85000.0
    DEFAULT_HEAT_OF_H2O_ABSORPTION_J_MOL = -40650.0
    DEFAULT_MAX_CO2_LOADING_MOL_CO2_PER_MOL_AMINE = 0.4
    DEFAULT_MAX_H2O_LOADING_KG_H2O_PER_KG_AMINE_SOLUTION = 0.1
    DEFAULT_ADSORPTION_RATE_CONSTANT_CO2 = 1.0e-7
    DEFAULT_ADSORPTION_RATE_CONSTANT_H2O = 5.0e-8
    DEFAULT_DESORPTION_RATE_CONSTANT_CO2 = 1.0e-4
    DEFAULT_DESORPTION_RATE_CONSTANT_H2O = 5.0e-5
    DEFAULT_REGENERATION_ENERGY_DEMAND_J_PER_KG_CO2 = 3.5e6
    DEFAULT_COOLING_POWER_FACTOR_W_PER_KG_K_DIFF = 10.0
    DEFAULT_COOLING_SYSTEM_COP = 2.0
    DEFAULT_ADSORPTION_TEMP_K = 273.15 + 40.0
    DEFAULT_DESORPTION_TEMP_K = 273.15 + 120.0
    DEFAULT_COOLING_TEMP_K = DEFAULT_ADSORPTION_TEMP_K
    DEFAULT_ADSORPTION_CYCLE_TIME_S = 3600.0
    DEFAULT_DESORPTION_CYCLE_TIME_S = 1800.0
    DEFAULT_COOLING_CYCLE_TIME_S = 900.0

    _ADSORPTION_PHASE = "adsorption"
    _DESORPTION_PHASE = "desorption"
    _COOLING_PHASE = "cooling"

    _NUMERICAL_STABILITY_FACTOR = 1.0 - 1e-7  # Factor to leave a tiny amount to avoid float issues

    def __init__(self,
                 name: str,
                 power_source: PowerSource,
                 parent_air_compartment: AirCompartment,
                 bed_volume_m3: float,
                 amine_solution_mass_kg: float,
                 amine_concentration_wt_pct: float,
                 adsorption_target_temperature_k: float = DEFAULT_ADSORPTION_TEMP_K,
                 desorption_target_temperature_k: float = DEFAULT_DESORPTION_TEMP_K,
                 cooling_target_temperature_k: float = DEFAULT_COOLING_TEMP_K,
                 adsorption_cycle_time_s: float = DEFAULT_ADSORPTION_CYCLE_TIME_S,
                 desorption_cycle_time_s: float = DEFAULT_DESORPTION_CYCLE_TIME_S,
                 cooling_cycle_time_s: float = DEFAULT_COOLING_CYCLE_TIME_S,
                 amine_molar_mass_kg_mol: float = DEFAULT_AMINE_MOLAR_MASS_KG_MOL,
                 amine_solution_density_kg_m3: float = DEFAULT_AMINE_SOLUTION_DENSITY_KG_M3,
                 amine_solution_specific_heat_j_kg_k: float = DEFAULT_AMINE_SOLUTION_SPECIFIC_HEAT_J_KG_K,
                 heat_of_co2_absorption_j_mol: float = DEFAULT_HEAT_OF_CO2_ABSORPTION_J_MOL,
                 heat_of_h2o_absorption_j_mol: float = DEFAULT_HEAT_OF_H2O_ABSORPTION_J_MOL,
                 max_co2_loading_mol_co2_per_mol_amine: float = DEFAULT_MAX_CO2_LOADING_MOL_CO2_PER_MOL_AMINE,
                 max_h2o_loading_kg_h2o_per_kg_amine_solution: float = DEFAULT_MAX_H2O_LOADING_KG_H2O_PER_KG_AMINE_SOLUTION,
                 adsorption_rate_constant_co2: float = DEFAULT_ADSORPTION_RATE_CONSTANT_CO2,
                 adsorption_rate_constant_h2o: float = DEFAULT_ADSORPTION_RATE_CONSTANT_H2O,
                 desorption_rate_constant_co2: float = DEFAULT_DESORPTION_RATE_CONSTANT_CO2,
                 desorption_rate_constant_h2o: float = DEFAULT_DESORPTION_RATE_CONSTANT_H2O,
                 regeneration_energy_demand_j_per_kg_co2: float = DEFAULT_REGENERATION_ENERGY_DEMAND_J_PER_KG_CO2,
                 cooling_power_factor_w_per_kg_k_diff: float = DEFAULT_COOLING_POWER_FACTOR_W_PER_KG_K_DIFF,
                 cooling_system_cop: float = DEFAULT_COOLING_SYSTEM_COP
                 ):
        super().__init__(name, power_source)
        self._parent = parent_air_compartment
        self.bed_volume_m3 = bed_volume_m3
        self.amine_solution_mass_kg = amine_solution_mass_kg
        self.amine_concentration_wt_pct = amine_concentration_wt_pct
        self.amine_molar_mass_kg_mol = amine_molar_mass_kg_mol
        self.amine_solution_density_kg_m3 = amine_solution_density_kg_m3
        self.amine_solution_specific_heat_j_kg_k = amine_solution_specific_heat_j_kg_k
        self.heat_of_co2_absorption_j_mol = heat_of_co2_absorption_j_mol
        self.heat_of_h2o_absorption_j_mol = heat_of_h2o_absorption_j_mol
        self.max_co2_loading_mol_co2_per_mol_amine = max_co2_loading_mol_co2_per_mol_amine
        self.max_h2o_loading_kg_h2o_per_kg_amine_solution = max_h2o_loading_kg_h2o_per_kg_amine_solution
        self.adsorption_rate_constant_co2 = adsorption_rate_constant_co2
        self.adsorption_rate_constant_h2o = adsorption_rate_constant_h2o
        self.desorption_rate_constant_co2 = desorption_rate_constant_co2
        self.desorption_rate_constant_h2o = desorption_rate_constant_h2o
        self.regeneration_energy_demand_j_per_kg_co2 = regeneration_energy_demand_j_per_kg_co2
        self.cooling_power_factor_w_per_kg_k_diff = cooling_power_factor_w_per_kg_k_diff
        self.cooling_system_cop = cooling_system_cop
        self._adsorption_target_temperature_k = adsorption_target_temperature_k
        self._desorption_target_temperature_k = desorption_target_temperature_k
        self._cooling_target_temperature_k = cooling_target_temperature_k
        self._adsorption_cycle_time_s = adsorption_cycle_time_s
        self._desorption_cycle_time_s = desorption_cycle_time_s
        self._cooling_cycle_time_s = cooling_cycle_time_s
        self._current_phase = self._ADSORPTION_PHASE
        self._time_in_current_phase_s = 0.0
        self._bed_temperature_k = parent_air_compartment.get_temperature() if parent_air_compartment else self._adsorption_target_temperature_k
        self._co2_adsorbed_mass_kg = 0.0
        self._h2o_adsorbed_mass_kg = 0.0
        self.mass_co2_ready_for_collection_kg = 0.0
        self.mass_h2o_ready_for_collection_kg = 0.0

        self._mass_amine_in_solution_kg = self.amine_solution_mass_kg * (self.amine_concentration_wt_pct / 100.0)
        if self.amine_molar_mass_kg_mol > 1e-9:
            self._moles_amine_total_in_solution = self._mass_amine_in_solution_kg / self.amine_molar_mass_kg_mol
        else:
            self._moles_amine_total_in_solution = 0.0

        if self._moles_amine_total_in_solution > 0 and self.CO2_MOLAR_MASS_KG_MOL > 1e-9:
            self._max_co2_capacity_kg = self._moles_amine_total_in_solution * \
                                        self.max_co2_loading_mol_co2_per_mol_amine * \
                                        self.CO2_MOLAR_MASS_KG_MOL
        else:
            self._max_co2_capacity_kg = 0.0

        self._max_h2o_capacity_kg = self.amine_solution_mass_kg * self.max_h2o_loading_kg_h2o_per_kg_amine_solution
        self._verify_initial_conditions()

    def _verify_initial_conditions(self):
        if self.power_source is None: raise ValueError("Power source cannot be None.")
        if self._parent is None: raise ValueError("Parent air compartment cannot be None.")
        if not self.bed_volume_m3 > 0: raise ValueError(f"Bed volume must be positive: {self.bed_volume_m3}")
        if not self.CO2_MOLAR_MASS_KG_MOL > 1e-9: raise ValueError("CO2_MOLAR_MASS_KG_MOL is not valid.")
        if not self.H2O_MOLAR_MASS_KG_MOL > 1e-9: raise ValueError("H2O_MOLAR_MASS_KG_MOL is not valid.")

    def update(self, dt: float = 0.0333) -> float:
        if dt <= 0: return 0.0
        self._time_in_current_phase_s += dt
        net_heat_produced_j = 0.0

        if self._current_phase == self._ADSORPTION_PHASE:
            net_heat_produced_j = self._adsorption_step(dt)
            if self._time_in_current_phase_s >= self._adsorption_cycle_time_s:
                self._current_phase = self._DESORPTION_PHASE
                self._time_in_current_phase_s = 0.0
        elif self._current_phase == self._DESORPTION_PHASE:
            net_heat_produced_j = self._desorption_step(dt)
            if self._time_in_current_phase_s >= self._desorption_cycle_time_s:
                self._current_phase = self._COOLING_PHASE
                self._time_in_current_phase_s = 0.0
        elif self._current_phase == self._COOLING_PHASE:
            net_heat_produced_j = self._cooling_step(dt)
            if self._time_in_current_phase_s >= self._cooling_cycle_time_s:
                self._current_phase = self._ADSORPTION_PHASE
                self._time_in_current_phase_s = 0.0
        return net_heat_produced_j

    def _adsorption_step(self, dt: float) -> float:
        co2_partial_pressure_pa = self._parent.get_co2_pressure()
        h2o_partial_pressure_pa = self._parent.get_h2o_pressure()
        max_co2_available_in_parent_kg = self._parent.get_co2_mass()
        max_h2o_available_in_parent_kg = self._parent.get_h2o_mass()

        # --- CO2 Adsorption ---
        remaining_co2_capacity_in_bed_kg = max(0.0, self._max_co2_capacity_kg - self._co2_adsorbed_mass_kg)
        potential_co2_adsorption_rate_kg_s = self.adsorption_rate_constant_co2 * \
                                             co2_partial_pressure_pa * self.bed_volume_m3
        co2_to_adsorb_this_dt_based_on_rate_kg = potential_co2_adsorption_rate_kg_s * dt

        # Tentative amount based on rate and bed capacity
        co2_adsorbed_this_step_kg = min(co2_to_adsorb_this_dt_based_on_rate_kg, remaining_co2_capacity_in_bed_kg)

        # Limit by what's available in the parent, ensuring stability
        if co2_adsorbed_this_step_kg >= max_co2_available_in_parent_kg:
            # If trying to take more than or equal to what's available
            if max_co2_available_in_parent_kg > 1e-12:  # Only apply factor if a meaningful amount is there
                co2_adsorbed_this_step_kg = max_co2_available_in_parent_kg * self._NUMERICAL_STABILITY_FACTOR
            else:  # If available is negligible or zero, take what's there (which is negligible or zero)
                co2_adsorbed_this_step_kg = max_co2_available_in_parent_kg

        co2_adsorbed_this_step_kg = max(0.0, co2_adsorbed_this_step_kg)  # Ensure non-negative

        self._co2_adsorbed_mass_kg += co2_adsorbed_this_step_kg
        co2_adsorption_rate_kg_s_actual = co2_adsorbed_this_step_kg / dt if dt > 1e-9 else 0.0

        # --- H2O Adsorption ---
        remaining_h2o_capacity_in_bed_kg = max(0.0, self._max_h2o_capacity_kg - self._h2o_adsorbed_mass_kg)
        potential_h2o_adsorption_rate_kg_s = self.adsorption_rate_constant_h2o * \
                                             h2o_partial_pressure_pa * self.bed_volume_m3
        h2o_to_adsorb_this_dt_based_on_rate_kg = potential_h2o_adsorption_rate_kg_s * dt

        h2o_adsorbed_this_step_kg = min(h2o_to_adsorb_this_dt_based_on_rate_kg, remaining_h2o_capacity_in_bed_kg)

        if h2o_adsorbed_this_step_kg >= max_h2o_available_in_parent_kg:
            if max_h2o_available_in_parent_kg > 1e-12:
                h2o_adsorbed_this_step_kg = max_h2o_available_in_parent_kg * self._NUMERICAL_STABILITY_FACTOR
            else:
                h2o_adsorbed_this_step_kg = max_h2o_available_in_parent_kg

        h2o_adsorbed_this_step_kg = max(0.0, h2o_adsorbed_this_step_kg)

        self._h2o_adsorbed_mass_kg += h2o_adsorbed_this_step_kg
        h2o_adsorption_rate_kg_s_actual = h2o_adsorbed_this_step_kg / dt if dt > 1e-9 else 0.0

        fluxes_to_parent = np.zeros(4, dtype=float)
        fluxes_to_parent[air.CO2_INDEX] = -co2_adsorption_rate_kg_s_actual
        fluxes_to_parent[air.H2O_INDEX] = -h2o_adsorption_rate_kg_s_actual
        self._parent.apply_flux(fluxes_to_parent, dt, mode="mass")

        co2_moles_adsorbed = co2_adsorbed_this_step_kg / self.CO2_MOLAR_MASS_KG_MOL if self.CO2_MOLAR_MASS_KG_MOL > 1e-9 else 0.0
        h2o_moles_adsorbed = h2o_adsorbed_this_step_kg / self.H2O_MOLAR_MASS_KG_MOL if self.H2O_MOLAR_MASS_KG_MOL > 1e-9 else 0.0

        heat_from_co2_adsorption_j = co2_moles_adsorbed * self.heat_of_co2_absorption_j_mol
        heat_from_h2o_adsorption_j = h2o_moles_adsorbed * self.heat_of_h2o_absorption_j_mol
        total_heat_released_j = -(heat_from_co2_adsorption_j + heat_from_h2o_adsorption_j)

        if self.amine_solution_mass_kg > 0 and self.amine_solution_specific_heat_j_kg_k > 0:
            delta_temp_k = total_heat_released_j / (
                        self.amine_solution_mass_kg * self.amine_solution_specific_heat_j_kg_k)
            self._bed_temperature_k += delta_temp_k

        self._bed_temperature_k = min(self._bed_temperature_k, self._desorption_target_temperature_k + 50.0)
        return total_heat_released_j

    def _desorption_step(self, dt: float) -> float:
        net_heat_produced_by_subsystem_j = 0.0
        if self._bed_temperature_k < self._desorption_target_temperature_k:
            temp_increase_needed_k = self._desorption_target_temperature_k - self._bed_temperature_k
            max_heating_rate_k_s = 2.0
            max_temp_increase_this_step_k = max_heating_rate_k_s * dt
            actual_temp_increase_k = max(0.0, min(temp_increase_needed_k, max_temp_increase_this_step_k))

            if self.amine_solution_mass_kg > 0 and self.amine_solution_specific_heat_j_kg_k > 0:
                thermal_energy_for_heating_j = actual_temp_increase_k * \
                                               self.amine_solution_mass_kg * \
                                               self.amine_solution_specific_heat_j_kg_k
                energy_consumed_actual_j = self.power_source.consume_heat(thermal_energy_for_heating_j, dt=dt,
                                                                          mode="energy")
                if thermal_energy_for_heating_j > 1e-9:
                    proportion_heated = energy_consumed_actual_j / thermal_energy_for_heating_j
                    self._bed_temperature_k += actual_temp_increase_k * proportion_heated

        if self._bed_temperature_k >= (self._desorption_target_temperature_k - 5.0):
            potential_co2_desorption_rate_kg_s = self.desorption_rate_constant_co2 * self._co2_adsorbed_mass_kg
            co2_desorbed_this_step_kg = max(0.0,
                                            min(potential_co2_desorption_rate_kg_s * dt, self._co2_adsorbed_mass_kg))
            potential_h2o_desorption_rate_kg_s = self.desorption_rate_constant_h2o * self._h2o_adsorbed_mass_kg
            h2o_desorbed_this_step_kg = max(0.0,
                                            min(potential_h2o_desorption_rate_kg_s * dt, self._h2o_adsorbed_mass_kg))

            thermal_energy_demand_for_desorption_j = 0.0
            if self.regeneration_energy_demand_j_per_kg_co2 > 0 and co2_desorbed_this_step_kg > 0:
                thermal_energy_demand_for_desorption_j = co2_desorbed_this_step_kg * self.regeneration_energy_demand_j_per_kg_co2

            energy_consumed_desorption_actual_j = 0.0
            if thermal_energy_demand_for_desorption_j > 0:
                energy_consumed_desorption_actual_j = self.power_source.consume_heat(
                    thermal_energy_demand_for_desorption_j, dt=dt, mode="energy")

            proportion_desorbed = 1.0
            if thermal_energy_demand_for_desorption_j > 1e-9:
                proportion_desorbed = energy_consumed_desorption_actual_j / thermal_energy_demand_for_desorption_j
            elif co2_desorbed_this_step_kg > 0:
                proportion_desorbed = 0.0

            co2_desorbed_this_step_kg *= proportion_desorbed
            h2o_desorbed_this_step_kg *= proportion_desorbed

            self._co2_adsorbed_mass_kg -= co2_desorbed_this_step_kg
            self._h2o_adsorbed_mass_kg -= h2o_desorbed_this_step_kg

            self.mass_co2_ready_for_collection_kg += co2_desorbed_this_step_kg
            self.mass_h2o_ready_for_collection_kg += h2o_desorbed_this_step_kg

            net_heat_produced_by_subsystem_j -= energy_consumed_desorption_actual_j
        return net_heat_produced_by_subsystem_j

    def _cooling_step(self, dt: float) -> float:
        net_heat_produced_by_subsystem_j = 0.0
        if self._bed_temperature_k > self._cooling_target_temperature_k:
            temp_difference_to_target_k = self._bed_temperature_k - self._cooling_target_temperature_k

            cooling_electrical_power_w = 0.0
            if self.amine_solution_mass_kg > 0:
                cooling_electrical_power_w = self.cooling_power_factor_w_per_kg_k_diff * \
                                             self.amine_solution_mass_kg * temp_difference_to_target_k
            cooling_electrical_power_w = max(0.0, cooling_electrical_power_w)

            electrical_energy_demanded_j = cooling_electrical_power_w * dt
            actual_electrical_energy_consumed_j = self.power_source.consume_electricity(electrical_energy_demanded_j,
                                                                                        dt=dt, mode="energy")

            heat_removed_from_bed_j = 0.0
            if self.cooling_system_cop > 1e-9:
                heat_removed_from_bed_j = self.cooling_system_cop * actual_electrical_energy_consumed_j

            actual_heat_removed_j_final = 0.0
            if self.amine_solution_mass_kg > 0 and self.amine_solution_specific_heat_j_kg_k > 0:
                potential_temp_decrease_k = heat_removed_from_bed_j / \
                                            (self.amine_solution_mass_kg * self.amine_solution_specific_heat_j_kg_k)
                actual_temp_decrease_k = min(potential_temp_decrease_k, temp_difference_to_target_k)
                actual_temp_decrease_k = max(0.0, actual_temp_decrease_k)
                self._bed_temperature_k -= actual_temp_decrease_k
                actual_heat_removed_j_final = actual_temp_decrease_k * \
                                              self.amine_solution_mass_kg * self.amine_solution_specific_heat_j_kg_k

            net_heat_produced_by_subsystem_j = actual_heat_removed_j_final + actual_electrical_energy_consumed_j
        return net_heat_produced_by_subsystem_j

    def collect(self, amount_co2_kg: float, amount_h2o_kg: float, dt: float = 0.0333, mode: str = "flux") -> tuple[
        float, float]:
        co2_to_remove_kg = 0.0
        h2o_to_remove_kg = 0.0
        if mode == "flux":
            co2_to_remove_kg = amount_co2_kg * dt
            h2o_to_remove_kg = amount_h2o_kg * dt
        elif mode == "amount":
            co2_to_remove_kg = amount_co2_kg
            h2o_to_remove_kg = amount_h2o_kg
        else:
            raise ValueError(f"Invalid mode '{mode}' for collect method. Use 'flux' or 'amount'.")
        actual_co2_removed_kg = max(0.0, min(co2_to_remove_kg, self.mass_co2_ready_for_collection_kg))
        actual_h2o_removed_kg = max(0.0, min(h2o_to_remove_kg, self.mass_h2o_ready_for_collection_kg))
        self.mass_co2_ready_for_collection_kg -= actual_co2_removed_kg
        self.mass_h2o_ready_for_collection_kg -= actual_h2o_removed_kg
        return actual_co2_removed_kg, actual_h2o_removed_kg

    def get_bed_temperature_k(self) -> float:
        return self._bed_temperature_k

    def get_co2_adsorbed_mass_kg(self) -> float:
        return self._co2_adsorbed_mass_kg

    def get_h2o_adsorbed_mass_kg(self) -> float:
        return self._h2o_adsorbed_mass_kg

    def get_current_phase(self) -> str:
        return self._current_phase

    def get_time_in_current_phase_s(self) -> float:
        return self._time_in_current_phase_s

    def get_co2_loading_mol_per_mol_amine(self) -> float:
        if self._moles_amine_total_in_solution < 1e-9 or self.CO2_MOLAR_MASS_KG_MOL < 1e-9: return 0.0
        moles_co2_adsorbed = self._co2_adsorbed_mass_kg / self.CO2_MOLAR_MASS_KG_MOL
        return moles_co2_adsorbed / self._moles_amine_total_in_solution

    def get_h2o_loading_kg_per_kg_solution(self) -> float:
        if self.amine_solution_mass_kg < 1e-9: return 0.0
        return self._h2o_adsorbed_mass_kg / self.amine_solution_mass_kg

