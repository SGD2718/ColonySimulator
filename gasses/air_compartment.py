import air
import numpy as np
import chemicals as chem


class AirCompartment:
    from air_graph import AirGraph

    def __init__(self,
                 parent: AirGraph | None,
                 name: str,
                 volume: float,
                 **kwargs):
        self.parent = parent
        self.name = name
        self.volume = volume
        self.filter = kwargs.get('filter', np.ones((4,), dtype=bool))

        self.densities = np.zeros((4,), dtype=float)

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return self.name == other

    def get_temperature(self):
        return self.parent.get_temperature()

    def get_density(self, index: int | None = None) -> float:
        if index is None:
            return np.sum(self.densities)
        return float(self.densities[index])

    def get_o2_density(self) -> float:
        return self.get_density(air.O2_INDEX)

    def get_co2_density(self) -> float:
        return self.get_density(air.CO2_INDEX)

    def get_n2_density(self) -> float:
        return self.get_density(air.N2_INDEX)

    def get_h2o_density(self) -> float:
        return self.get_density(air.H2O_INDEX)

    def get_densities(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        return self.densities

    def get_mass(self, index: int | None = None) -> float:
        if index is None:
            return self.volume * np.sum(self.densities)
        return float(self.volume * self.densities[index])

    def get_masses(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        return self.densities * self.volume

    def get_o2_mass(self) -> float:
        return self.get_mass(air.O2_INDEX)

    def get_co2_mass(self) -> float:
        return self.get_mass(air.CO2_INDEX)

    def get_h2o_mass(self) -> float:
        return self.get_mass(air.H2O_INDEX)

    def get_n2_mass(self) -> float:
        return self.get_mass(air.N2_INDEX)

    def get_pressure(self, index: int | None = None) -> float:
        # P = RT / rho
        if index is None:
            return self.parent.get_temperature() * np.sum(air.GAS_CONSTANTS * self.densities)
        return self.parent.get_temperature() * float(air.GAS_CONSTANTS[index]) * float(self.densities[index])

    def get_pressures(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        # P = RT / rho
        return self.parent.get_temperature() * air.GAS_CONSTANTS * self.densities

    def get_o2_pressure(self) -> float:
        return self.get_pressure(air.O2_INDEX)

    def get_co2_pressure(self) -> float:
        return self.get_pressure(air.CO2_INDEX)

    def get_n2_pressure(self) -> float:
        return self.get_pressure(air.N2_INDEX)

    def get_h2o_pressure(self) -> float:
        return self.get_pressure(air.H2O_INDEX)

    def get_volume(self) -> float:
        return self.volume

    def apply_flux(self,
                   fluxes: np.ndarray[tuple[int, ...], np.dtype[float]],
                   dt: float = 0.033,
                   **kwargs) -> None:
        """
        Applies flux changes o2 and co2 density
        :param fluxes: gas fluxes
        :param dt: time step since last update
        :param mode: mode to apply ("density", "mass")
        """
        mode = kwargs.get("mode", "density")

        if mode == "density":
            self.densities += fluxes * dt
        else:
            self.densities += fluxes * dt / self.volume

        assert np.all(self.densities >= 0)

    def add_gas(self,
                amounts: np.ndarray[tuple[int, ...], np.dtype[float]],
                **kwargs) -> None:

        mode = kwargs.get("mode", "density")
        if mode == "density":
            self.densities += amounts
        else:
            self.densities += amounts / self.volume

        assert np.all(self.densities >= 0)



class Atmosphere(AirCompartment):
    PRESSURE = 610  # Pa
    DENSITY = 0.0162  # kg/m^3
    O2_PROPORTION = 0.0013
    CO2_PROPORTION = 0.9532
    N2_PROPORTION = 0.027
    H2O_PROPORTION = 0.0003

    O2_MASS = O2_PROPORTION * chem.O2.molar_mass_kg_mol
    CO2_MASS = CO2_PROPORTION * chem.CO2.molar_mass_kg_mol
    N2_MASS = N2_PROPORTION * chem.N2.molar_mass_kg_mol
    H2O_MASS = H2O_PROPORTION * chem.H2O.molar_mass_kg_mol
    MOLAR_MASS = O2_MASS + CO2_MASS + N2_MASS + H2O_MASS

    O2_DENSITY = DENSITY * O2_MASS / MOLAR_MASS
    CO2_DENSITY = DENSITY * CO2_MASS / MOLAR_MASS
    N2_DENSITY = DENSITY * N2_MASS / MOLAR_MASS
    H2O_DENSITY = DENSITY * H2O_MASS / MOLAR_MASS

    # ρX = kg X / m^3 =
    # (mol X / mol atm) * (kg X / mol X) * (mol atm / kg atm) * (kg atm / m^3 atm)
    #        C_X        *      M_X       /        M_atm       *        ρ_atm

    DENSITIES = np.asarray([O2_DENSITY, CO2_DENSITY, N2_DENSITY, H2O_DENSITY], dtype=float)

    def __init__(self, temperature: float):
        super().__init__(None, "Atmosphere", float('inf'))
        self.temperature = temperature

    def get_o2_density(self) -> float:
        return Atmosphere.O2_DENSITY

    def get_n2_density(self) -> float:
        return Atmosphere.N2_DENSITY

    def get_co2_density(self) -> float:
        return Atmosphere.CO2_DENSITY

    def get_h2o_density(self) -> float:
        return Atmosphere.H2O_DENSITY

    def get_density(self, index: int | None = None) -> float:
        if index is None:
            return Atmosphere.DENSITY
        return float(Atmosphere.DENSITIES[index])

    def get_densities(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        return Atmosphere.DENSITIES

    def get_o2_mass(self) -> float:
        return 0

    def get_co2_mass(self) -> float:
        return 0

    def get_n2_mass(self) -> float:
        return 0

    def get_h2o_mass(self) -> float:
        return 0

    def get_mass(self, index: int | None = None) -> float:
        return 0

    def get_masses(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        return np.zeros((4,), dtype=float)

    def get_pressure(self, index: int | None = None) -> float:
        # P = RT / rho
        if index is None:
            return Atmosphere.PRESSURE
        return self.temperature * float(air.GAS_CONSTANTS[index]) * float(Atmosphere.DENSITIES[index])

    def get_pressures(self) -> np.ndarray[tuple[int, ...], np.dtype[float]]:
        # P = RT / rho
        return self.temperature * air.GAS_CONSTANTS * Atmosphere.DENSITIES

    def get_o2_pressure(self) -> float:
        return self.get_pressure(air.O2_INDEX)

    def get_co2_pressure(self) -> float:
        return self.get_pressure(air.CO2_INDEX)

    def get_n2_pressure(self) -> float:
        return self.get_pressure(air.N2_INDEX)

    def get_h2o_pressure(self) -> float:
        return self.get_pressure(air.H2O_INDEX)

    def get_temperature(self):
        return self.temperature

    def apply_flux(self,
                   fluxes: np.ndarray[tuple[int, ...], np.dtype[float]],
                   dt: float = 0.033,
                   **kwargs) -> None:
        pass

    def add_gas(self,
                 masses: np.ndarray[tuple[int, ...], np.dtype[float]],
                 **kwargs) -> None:
        pass


print(f"O2: {Atmosphere.O2_DENSITY} kg/m^3")
print(f"CO2: {Atmosphere.CO2_DENSITY} kg/m^3")
print(f"N2: {Atmosphere.N2_DENSITY} kg/m^3")
