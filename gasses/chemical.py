class Chemical:
    SUBSCRIPTS_MAP = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')

    def __init__(self, name: str, molar_mass: float):
        self.name = name
        self.molar_mass = molar_mass
        self.molar_mass_kg_mol = molar_mass * 1000

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __add__(self, other):
        """
        chemical1.__add__(chemical2) -> chemical1 + chemical2
        adds chemical1 to chemical2
        :param other: another chemical.
        :type other: Chemical
        :return: a new chemical.
        :rtype: Chemical
        """
        return Chemical(self.name + other.name, self.molar_mass + other.molar_mass)

    def __mul__(self, count: int):
        """
        chemical1.__mul__(count) -> chemical1 * count
        :param count: number of times to multiply
        :return: chemical1 * count
        :rtype: Chemical
        """
        subscript = str(count).translate(Chemical.SUBSCRIPTS_MAP)
        if len(self.name) <= 2:
            return Chemical(f'{self.name}{subscript}', self.molar_mass * count)
        return Chemical(f'({self.name}){subscript}', self.molar_mass * count)


class Gas(Chemical):
    UNIVERSAL_GAS_CONSTANT = 8314.4598

    def __init__(self, chemical: Chemical, specific_heat_table: dict[float: float]):
        super().__init__(chemical.name, chemical.molar_mass)

        self.gas_constant: float = Gas.UNIVERSAL_GAS_CONSTANT / self.molar_mass
        self._temps, self._specific_heats = zip(*sorted(specific_heat_table.items(), key=lambda item: item[0]))

    def specific_heat_capacity(self, temperature: float) -> float:
        if temperature < self._temps[0]:
            dc_dT = (self._specific_heats[1] - self._specific_heats[0]) / (self._temps[1] - self._temps[0])
            return dc_dT * (temperature - self._temps[0]) + self._specific_heats[0]

        i = 0
        while self._temps[i + 1] < temperature and i < len(self._temps) - 1:
            i += 1

        dc_dT = (self._specific_heats[i+1] - self._specific_heats[i]) / (self._temps[i+1] - self._temps[i])
        return dc_dT * (temperature - self._temps[i]) + self._specific_heats[i]

