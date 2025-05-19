class Door:
    def __init__(self, name, is_pressure_sealed: bool, area: float):
        self.is_open = False
        self.is_pressure_sealed = is_pressure_sealed
        self.area = area

    