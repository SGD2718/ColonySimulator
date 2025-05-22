import numpy as np
import chemicals as chem


O2_INDEX = 0
CO2_INDEX = 1
N2_INDEX = 2
H2O_INDEX = 3

GAS_CONSTANTS: np.ndarray[tuple[int, ...], np.dtype[float]] = np.asarray(
    [chem.O2.gas_constant, chem.CO2.gas_constant, chem.N2.gas_constant, chem.H2O.gas_constant],
    dtype=float
)
