class NuclearReactor:
    def __init__(self):
        self.fuel = 100
        self.fuel_consumption = 1
        self.electrical_output = 0
        self.heat_output = 0

        self.heat_tolerance = 0

    def get_electrical_power(self):
        return self.electrical_output

    def get_heat_power(self):
        return self.heat_output
