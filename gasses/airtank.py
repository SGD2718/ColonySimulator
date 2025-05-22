import numpy as np

from air_compartment import AirCompartment
from air_graph import AirGraph
import air
import chemicals as chem


class AirTank(AirCompartment):
    def __init__(self,
                 parent: AirGraph | None,
                 name: str,
                 volume: float,
                 **kwargs):
        super().__init__(parent, name, volume, **kwargs)
        self.max_pressure = kwargs.get('max_pressure', 1e6)
        self._flux = np.zeros((4,), float)

    def read_flux(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        tmp = np.copy(self._flux)
        self._flux = np.zeros((4,), float)
        return tmp

    def apply_flux(self,
                   fluxes: np.ndarray[tuple[int, ...], np.dtype[float]],
                   dt: float = 0.033,
                   **kwargs):
        mode = kwargs.get('mode', 'density')

        delta = fluxes if mode == "density" else fluxes / self.volume
        self.densities += delta * dt
        self._flux += delta

        assert np.all(self.densities >= 0)

    def get_max_pressure(self) -> float:
        return self.max_pressure

    def is_full(self, dt: float = 0.0333) -> bool:
        """
        Checks if the air tank is full or will be full at some point in the future
        :param dt: amount of time to advance the air tank before checking for fullness
        :return: True if air tank will be full, False otherwise
        """
        projected_pressure = (self.parent.get_temperature() *
                              np.sum(air.GAS_CONSTANTS * (self.densities + self._flux * dt)))
        return projected_pressure >= self.max_pressure

    def fill_to_capacity(self,
                         source: np.ndarray[tuple[int, ...], np.dtype[float]],
                         dt: float = 0.0333
                         ) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        """
        Fills the tank so that it will reach capacity at the next update
        (using the last flux self._flux) or until source is drained.
        The added gas has the same species‐mass ratios as `source`.

        Method was written by ChatGPT o4-mini because it's like 12:46 AM

        :param source: gas‐mass array (one entry per species)
        :param dt:      look‐ahead time for fullness check
        :return:        array of mass added per species (shape matches `source`)
        """
        T = self.parent.get_temperature()
        R = air.GAS_CONSTANTS  # array of gas‐constants R_i
        V = self.volume  # tank volume

        # 1) Compute current S = sum_i R_i * density_i (after flux*dt)
        #    where density_i = mass_i / V
        densities_future = self.densities + self._flux * dt
        S_current = np.sum(R * densities_future)

        # 2) Compute target S_max = P_max / T
        S_max = self.max_pressure / T
        delta_S = S_max - S_current
        if delta_S <= 0:
            # Already at or above capacity
            return np.zeros_like(source)

        total_source = np.sum(source)
        if total_source <= 0:
            # No gas available
            return np.zeros_like(source)

        # 3) Species‐mass ratios in source
        ratios = source / total_source

        # 4) denom_raw = sum_i R_i * (ratios_i / V)  appears in
        #    delta_S = sum_i R_i * (Δm_i/V) = (M_total / V)*sum(R*ratios)
        denom_raw = np.sum(R * ratios)
        if denom_raw <= 0:
            # Can't raise pressure with these species
            return np.zeros_like(source)

        # 5) Total mass needed
        #    M_req = delta_S * V / denom_raw
        M_req = delta_S * V / denom_raw

        # 6) Cap at what's available
        M_add = min(M_req, total_source)

        # 7) Distribute mass according to source ratios
        delta_mass = ratios * M_add

        # 8) Update tank densities and source
        #    densities are mass/V, so Δdensity = Δmass/V
        self.densities += delta_mass / V
        source -= delta_mass

        self._flux = np.zeros((4,), dtype=float)

        return delta_mass


