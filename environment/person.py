import random


class Person:
    # https://oehha.ca.gov/media/downloads/crnr/chapter32012.pdf
    # https://www.desmos.com/calculator/mrln3plkkr
    MEAN_BREATHING_RATE_PER_BODY_MASS = 181.89295  # L/kg/day
    SCALE_BREATHING_RATE_PER_BODY_MASS = 36.15732  # L/kg/day

    def __init__(self, name, weight: float):
        self.name = name
        self.weight = weight

        self.o2_rate = 0
        self.co2_rate = 0



        self.energy = 0
        self.food = 0
        self.water = 0
        self.exercise = 0



