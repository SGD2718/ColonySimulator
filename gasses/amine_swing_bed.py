# amine_swing_bed.py
# Credit: ChatGPT, model o3
import math
from typing import Optional, List
import numpy as np

import chemicals as chem
import air
from gasses.sabatier_reactor import SabatierReactor

from subsystem import Subsystem
from gasses.air_compartment import AirCompartment
from power_source import PowerSource


class Sorbent:
    """
    Simple container for sorbent properties.
    All values are referenced to 25 °C (298 K).
    Units:
        k2                  m³·kmol⁻¹·s⁻¹
        henry_co2           kmol·m⁻³·kPa⁻¹
        delta_h_abs         kJ·kmol⁻¹
        density             kg·m⁻³ of packed bed (solids+voids)
    """
    def __init__(self,
                 name: str,
                 k2: float,
                 henry_co2: float,
                 delta_h_abs: float,
                 density: float,
                 default_void_frac: float = 0.36):
        self.name = name
        self.k2 = k2
        self.henry_co2 = henry_co2
        self.delta_h_abs = delta_h_abs              # kJ kmol⁻¹
        self.density = density
        self.void_frac = default_void_frac


# ---------------------------------------------------------------------------
#   Built-in sorbents (extend at will)
# ---------------------------------------------------------------------------
class Sorbents:
    """Library of built-in sorbents."""
    MEA_30WT = Sorbent(
        name="30 wt % MEA on polymer",
        k2=2.5e3,                      # m³ kmol⁻¹ s⁻¹  (20–30 °C)
        henry_co2=0.034,               # kmol m⁻³ kPa⁻¹
        delta_h_abs=96.0,              # kJ kmol⁻¹
        density=650                    # kg m⁻³ packed cartridge (solid + liquid)
    )


# ---------------------------------------------------------------------------
#   AmineSwingBed implementation
# ---------------------------------------------------------------------------
class AmineSwingBed(Subsystem):
    """
    Fast-cycle amine swing-bed CO₂/H₂O scrubber (CAMRAS-like).

    State vector per bed (all 25 °C linearisation):
        L_CO2      [kmol]  – sorbent loading of CO₂
        L_H2O      [kmol]  – sorbent loading of H₂O
        P_CO2_g    [kPa]   – gas CO₂ partial pressure in bed void
        P_H2O_g    [kPa]   – gas H₂O partial pressure in bed void
    """
    ROOM_TEMPERATURE = 298.15        # K

    # ---------- constructor ------------------------------------------------
    def __init__(self,
                 name: str,
                 power_source: PowerSource,
                 parent: AirCompartment,
                 sabatier_reactor_output: SabatierReactor = None,
                 **kwargs):
        """
        Parameters settable via kwargs (defaults = CAMRAS fast point):
            power_efficiency           – overall blower η_tot          (dimless)
            interface_area             – m² per bed
            bed_volume                 – m³ void volume per bed
            number_of_beds             – 2
            sorbent_mass               – kg per bed
            sorbent_material           – Sorbent object (defaults to 30 wt % MEA)
            operating_temperature      – K
            cycle_time                 – s  (full cycle: adsorb+desorb)
            mea_concentration          – kmol m⁻³ of amine in solution
            airflow_rate               – m³ s⁻¹ (per online bed in adsorption)
            active_beds                – list[int] of bed indices initially online
        """
        super().__init__(name, power_source)
        # Store room pointer for later interaction
        self._parent = parent
        self.sabatier_reactor_output = sabatier_reactor_output

        # ------------------------------------------------------------------
        # Configurable parameters (with defensible, high-performance defaults)
        # ------------------------------------------------------------------
        self.power_efficiency = kwargs.get("power_efficiency", 0.18)  # CAMRAS fan
        self.interface_area = kwargs.get("interface_area", 2.1)       # m²
        self.bed_volume = kwargs.get("bed_volume", 0.0030)            # m³ (void)
        self.number_of_beds = kwargs.get("number_of_beds", 2)
        self.sorbent_material: Sorbent = kwargs.get("sorbent_material", Sorbents.MEA_30WT)

        # If sorbent_mass omitted, compute from density*volume
        self.sorbent_mass = kwargs.get(
            "sorbent_mass",
            self.sorbent_material.density * self.bed_volume / (1 - self.sorbent_material.void_frac)
        )
        self.operating_temperature = kwargs.get("operating_temperature", self.ROOM_TEMPERATURE)
        self.cycle_time = kwargs.get("cycle_time", 780.0)             # 13 min full cycle
        self.mea_concentration = kwargs.get("mea_concentration", 5.0)  # kmol m⁻³
        self.airflow_rate = kwargs.get("airflow_rate", 0.0123)        # m³ s⁻¹
        self.desorption_vacuum_pressure = kwargs.get("desorption_vacuum_pressure", 0.2)  # kPa

        # bed scheduling
        self._phase_time = 0.0

        # Start all beds regenerated
        self._init_bed_states()

        # External conditions (can be overwritten via setters)
        self._p_tot_ext = 101.3      # kPa
        self._p_co2_ext = 0.4        # kPa  (≈ 3 mmHg)
        self._p_h2o_ext = 1.6        # kPa  (45 % RH)
        self._ext_temperature = self.operating_temperature

        # ------------------ run-time bookkeeping ---------------------------
        # beds currently online for adsorption (list of indices)
        self._active_beds = kwargs.get("active_beds",
                                       list(range(self.number_of_beds)))
        self._absorbing = True

        self.mass_co2_released = 0
        self.mass_h2o_released = 0

    # ------------------------------------------------------------------
    #            private helpers
    # ------------------------------------------------------------------
    def _init_bed_states(self):
        # per-bed state arrays; one entry per bed
        self._l_co2 = [0.0] * self.number_of_beds    # kmol
        self._l_h2o = [0.0] * self.number_of_beds    # kmol
        self._p_co2_g = [self._p_co2_ext] * self.number_of_beds
        self._p_h2o_g = [self._p_h2o_ext] * self.number_of_beds

    # ------------------------------------------------------------------
    #              property setters
    # ------------------------------------------------------------------
    def set_cycle_time(self, sec: float):
        self.cycle_time = max(60.0, float(sec))  # min 1 min

    def set_total_external_pressure(self, kpa: float):
        self._p_tot_ext = max(1.0, float(kpa))

    def set_external_co2_partial_pressure(self, kpa: float):
        self._p_co2_ext = max(0.0, float(kpa))

    def set_external_h2o_partial_pressure(self, kpa: float):
        self._p_h2o_ext = max(0.0, float(kpa))

    def set_absorbing_mode(self, absorbing: bool):
        self._absorbing = bool(absorbing)

    def set_desorption_vacuum_pressure(self, kpa: float):
        self.desorption_vacuum_pressure = max(0.01, float(kpa))

    def set_air_flow_rate(self, m3_s: float):
        self.airflow_rate = max(0.0, float(m3_s))

    def set_active_beds(self, active_beds: List[int]):
        self._active_beds = [b for b in active_beds if 0 <= b < self.number_of_beds]

    def set_external_temperature(self, kelvin: float):
        self._ext_temperature = max(250.0, float(kelvin))

    # ------------------------------------------------------------------
    #                         public interface
    # ------------------------------------------------------------------

    def collect(self, amount_co2: float, amount_h2o: float, dt: float = 0.0333,
                mode: str = "flux") -> tuple[float, float]:
        """
        Withdraw CO₂ and H₂O (kg) from internal stores.
          mode="flux":   arguments are kg s⁻¹, integrate over dt
          mode="amount": arguments are total kg to remove instantly
        Returns the actually withdrawn masses (kg).
        """
        if mode == "flux":
            req_co2 = amount_co2 * dt
            req_h2o = amount_h2o * dt
        else:  # "amount"
            req_co2 = amount_co2
            req_h2o = amount_h2o
        got_co2 = min(req_co2, self.mass_co2_released)
        got_h2o = min(req_h2o, self.mass_h2o_released)
        self.mass_co2_released -= got_co2
        self.mass_h2o_released -= got_h2o
        return got_co2, got_h2o

    def update(self, dt: float = 0.0333, **kwargs) -> float:
        """
        Advance simulation dt [s]; return heat released [J].
        """
        # Allow on-the-fly overrides
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

        # external environment may change
        self._update_external_pressures_and_temperatures()

        # choose σ for this half-cycle
        self._phase_time += dt
        half_cycle = self.cycle_time * 0.5
        if self._phase_time >= half_cycle:
            self._phase_time -= half_cycle
            self._absorbing = not self._absorbing

        sigma = 1 if self._absorbing else 0

        # ---------------- mass/power/heat balances ---------------------
        total_heat_j = 0.0
        for b in self._active_beds:
            if sigma == 1:                          # ADSORPTION
                h_gen = self._adsorption_step(b, dt)
            else:                                   # DESORPTION
                h_gen = self._desorption_step(b, dt)
            total_heat_j += h_gen

        # blower power (applied continuously)
        blower_power_w = self._blower_power()
        self.power_source.consume_electricity(blower_power_w, dt)

        # produce sensible heat into room
        total_heat_j += blower_power_w * dt  # fan motor → heat

        if self.sabatier_reactor_output is not None:
            self.sabatier_reactor_output.feed_reactants(self.mass_co2_released, 0, mode='amount')
            self.mass_co2_released = 0

        return total_heat_j

    # ==================================================================
    #                       core physics
    # ==================================================================
    def _adsorption_step(self, idx: int, dt: float) -> float:
        """Adsorb CO₂ + H₂O for one bed; return heat J."""
        sorb = self.sorbent_material
        # gas phase initial P_CO2 in bed (drive towards ext)
        p_co2 = self._p_co2_g[idx]
        p_h2o = self._p_h2o_g[idx]

        # mass-transfer driving force
        c_star = p_co2 / sorb.henry_co2
        l_co2_bulk = self._l_co2[idx] / self.bed_volume  # kmol m⁻³
        rate_mt = self.interface_area * 1.0e-4 * (c_star - l_co2_bulk)  # kmol s⁻¹

        # parallel reaction term
        rate_rxn = sorb.k2 * self.mea_concentration * p_co2  # kmol s⁻¹

        dot_l_co2 = rate_mt + rate_rxn
        self._l_co2[idx] += dot_l_co2 * dt

        # update gas partial pressure (simple perfect-mix tank model)
        vg = self.bed_volume
        r_specific = chem.Gas.UNIVERSAL_GAS_CONSTANT * 1e3  # J kmol⁻¹ K⁻¹
        n_co2_gas = p_co2 * vg / (r_specific / 1000 * self.operating_temperature)
        n_co2_gas -= dot_l_co2 * dt
        p_co2_new = max(0.001, n_co2_gas * (r_specific / 1000) *
                        self.operating_temperature / vg)
        self._p_co2_g[idx] = p_co2_new

        # approximate H₂O as purely mass transfer
        c_star_h2o = self._p_h2o_ext / 17.5  # Henry H2O constant
        l_h2o_bulk = self._l_h2o[idx] / self.bed_volume
        dot_l_h2o = self.interface_area * 1.0e-4 * (c_star_h2o - l_h2o_bulk)
        self._l_h2o[idx] += dot_l_h2o * dt

        # bookkeeping mass fluxes (kg s⁻¹)
        co2_mass_flux = dot_l_co2 * chem.CO2.molar_mass
        h2o_mass_flux = dot_l_h2o * chem.H2O.molar_mass
        # room mass balance
        self._parent.apply_flux(np.asarray([0,
                                            -co2_mass_flux,
                                            0,
                                            h2o_mass_flux], dtype=float),
                                dt,
                                mode="mass")

        heat_kj = dot_l_co2 * sorb.delta_h_abs
        return heat_kj * 1e3 * dt  # convert kJ → J

    def _desorption_step(self, idx: int, dt: float) -> float:
        """Vacuum-desorb: release load to space; return heat J (negative)."""
        # simple exponential blowdown of sorbent loading back to 0
        tau = self.cycle_time * 0.4
        released_co2 = self._l_co2[idx] * (1 - math.exp(-dt / tau))
        released_h2o = self._l_h2o[idx] * (1 - math.exp(-dt / tau))
        self._l_co2[idx] -= released_co2
        self._l_h2o[idx] -= released_h2o

        # Update gas to vacuum
        self._p_co2_g[idx] = self.desorption_vacuum_pressure
        self._p_h2o_g[idx] = self.desorption_vacuum_pressure

        self.mass_h2o_released += released_h2o * chem.H2O.molar_mass
        self.mass_co2_released += released_co2 * chem.CO2.molar_mass

        # desorption is slightly endothermic w.r.t. cabin
        heat_kj = -released_co2 * self.sorbent_material.delta_h_abs * 0.3
        return heat_kj * 1e3  # J

    # ------------------------------------------------------------------
    # blower power using QΔp/η (Ergun Δp estimate)
    # ------------------------------------------------------------------
    def _blower_power(self) -> float:
        v_face = self.airflow_rate / (self.interface_area / 2)  # divide because ½ beds online
        dp = 800.0 * (v_face / 0.35) ** 2                      # simple scaling to 0.9 kPa at 0.35 m/s
        return self.airflow_rate * dp / self.power_efficiency  # W

    # ------------------------------------------------------------------
    # placeholder for external env update (user will fill)
    # ------------------------------------------------------------------
    def _update_external_pressures_and_temperatures(self) -> None:
        self._ext_temperature = self._parent.get_temperature()
        pressures = self._parent.get_pressures()
        self._p_tot_ext = np.sum(pressures)
        self._p_co2_ext = pressures[air.CO2_INDEX]
        self._p_h2o_ext = pressures[air.H2O_INDEX]



