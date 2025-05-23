from gasses import air
from environment.room import Room

import gasses.chemicals as chem
import random
import numpy as np


class Person:
    # https://oehha.ca.gov/media/downloads/crnr/chapter32012.pdf
    # https://www.desmos.com/calculator/mrln3plkkr
    MEAN_BREATHING_RATE_PER_BODY_MASS = 0.18189295 / 86400  # m^3/kg/s
    SCALE_BREATHING_RATE_PER_BODY_MASS = 0.03615732 / 86400  # m^3/kg/s

    RESPIRATORY_QUOTIENT = 0.8
    PROPORTION_OF_O2_EXHALED = 0.76
    INTERNAL_H2O_SATURATION_DENSITY = 0.044  # kg/m^3

    INHALE_DURATION = 1.25  # seconds
    EXHALE_DURATION = 1.75  # seconds
    PAUSE_DURATION = 1.50   # seconds
    BREATHING_CYCLE = [INHALE_DURATION, EXHALE_DURATION, PAUSE_DURATION]
    BREATH_DURATION = sum(BREATHING_CYCLE)

    SEXES = ['male', 'female']
    SEX_DISTRIBUTION = [25, 1]  # male : female ratio

    BODY_MASS_MEANS = {
        'male': 80.4,
        'female': 63.4
    }

    BODY_MASS_STD_DEVS = {
        'male': 9.0,
        'female': 8.0
    }

    NAMES = {
        'male': [
            "Alexander", "Aleksei", "Anatoly", "Andrei", "Anton", "Arkady", "Arseny", "Artur", "Boris", "Daniil",
            "Denis", "Dmitry", "Eduard", "Egor", "Evgeny", "Fedor", "Filipp", "Gennady", "Georgy", "German", "Grigory",
            "Igor", "Ilya", "Ivan", "Kirill", "Konstantin", "Leonid", "Lev", "Maksim", "Matvei", "Mikhail", "Nikita",
            "Nikolai", "Oleg", "Pavel", "Petr", "Pyotr", "Roman", "Ruslan", "Savely", "Semyon", "Sergey", "Stanislav",
            "Stepan", "Timofey", "Vadim", "Valentin", "Valery", "Vasily", "Viktor", "Vitaly", "Vladimir", "Vladislav",
            "Vsevolod", "Vyacheslav", "Yaroslav", "Yuri", "Yegor", "Zahar", "Bogdan", "Aristarkh", "Rodion", "Gleb",
            "Trofim", "Avdey", "Nikifor", "Ignat", "Arkhip", "Timur", "Tikhon", "Platon", "Makar", "Miron", "Vasiliy",
            "Yulian", "Prokhor", "Anisim", "Demid", "Lavr", "Veniamin", "Elizar", "Fedot", "Kuzma", "Spiridon",
            "Nikandr", "Daniar", "Taras", "Anatol", "Evdokim", "Iosif", "Luka", "Ravil", "Svyatoslav", "Yermolai",
            "Zinovy", "Vladlen", "Kir", "Klim", "Osip", "Yuliy"
        ],
        'female': [
            "Anastasia", "Anna", "Alina", "Alla", "Alyona", "Angelina", "Antonina", "Arina", "Daria", "Diana",
            "Ekaterina", "Elena", "Elizaveta", "Evgeniya", "Galina", "Inna", "Irina", "Ksenia", "Kristina", "Larisa",
            "Lidia", "Lilia", "Lyubov", "Marina", "Maria", "Margarita", "Natalia", "Nadezhda", "Olga", "Oksana",
            "Polina", "Raisa", "Regina", "Svetlana", "Sofia", "Tatiana", "Taisiya", "Valentina", "Valeriya", "Vera",
            "Viktoria", "Yana", "Yulia", "Zinaida", "Zoya", "Agata", "Aglaya", "Albina", "Anastasiya", "Anfisa",
            "Apollinariya", "Avelina", "Avgusta", "Varvara", "Vasilisa", "Vladislava", "Veronika", "Violetta", "Darya",
            "Dominika", "Evdokiya", "Eseniya", "Faina", "Feodora", "Glafira", "Gordana", "Iya", "Izolda", "Kapitolina",
            "Kira", "Klavdia", "Lada", "Lidiya", "Liza", "Lyudmila", "Maya", "Melaniya", "Milana", "Miroslava", "Nika",
            "Nonna", "Olesya", "Pelageya", "Praskovya", "Radmila", "Rada", "Roza", "Ruslana", "Serafima", "Snezhana",
            "Stanislava", "Stefaniya", "Tamara", "Tatyana", "Ulyana", "Ustinya", "Varya", "Yevdokiya", "Yesenia",
            "Zhanna"
        ]
    }

    def __init__(self,
                 room: Room,
                 **kwargs):
        """
        :param room: Room in which the person is located
        :keyword name: name of the person (randomly selected by default)
        :keyword sex: sex of the person (randomly selected by default)
        :keyword weight: weight of the person in kg (randomly selected by default)
        """
        self.room: Room = room

        # Note that Russia heavily suppresses LGBTQ+ so that means
        # I don't have to model a gender gradient for the astronauts
        self.sex = kwargs.get('sex', random.choices(Person.SEXES, weights=Person.SEX_DISTRIBUTION)[0])
        self.name = kwargs.get('name', random.choice(Person.NAMES[self.sex]))
        self.weight = kwargs.get('weight', random.normalvariate(Person.BODY_MASS_MEANS[self.sex],
                                                                Person.BODY_MASS_STD_DEVS[self.sex]))

        self.breathing_rate = self.weight * np.random.logistic(Person.MEAN_BREATHING_RATE_PER_BODY_MASS,
                                                               Person.SCALE_BREATHING_RATE_PER_BODY_MASS)

        self.is_alive = True
        self.lung_composition = np.zeros((4,), dtype=float)

        # (inhale rate) = (breath duration) * (average breathing rate) / (inhale duration)
        # (exhale rate) = (breath duration) * (average breathing rate) / (exhale duration)
        self.inhale_rate = self.breathing_rate * Person.BREATH_DURATION / Person.INHALE_DURATION  # m^3 / s
        self.exhale_rate = np.zeros_like(self.lung_composition)

        self._breathing_state = 0
        self._time_elapsed_in_breathing_state = 0

    def update(self, dt: float = 0.0333):
        if self.is_alive:
            if self._breathing_state == 0:
                self._inhale(dt)
            elif self._breathing_state == 1:
                self._exhale(dt)
            else:
                self._pause(dt)

    def _inhale(self, dt: float = 0.0333):
        """
        inhale helper function
        :param dt: time step
        """

        dt_used = min(Person.BREATHING_CYCLE[self._breathing_state] - self._time_elapsed_in_breathing_state, dt)
        self._time_elapsed_in_breathing_state += dt_used

        volume = self.inhale_rate * dt_used
        masses_inhaled = self.room.get_densities() * volume
        self.room.add_gas(-masses_inhaled, mode='mass')

        o2_consumed_moles = (masses_inhaled[air.O2_INDEX](1 - Person.PROPORTION_OF_O2_EXHALED) /
                             chem.O2.molar_mass_kg_mol)
        co2_produced_kg = o2_consumed_moles * Person.RESPIRATORY_QUOTIENT * chem.CO2.molar_mass_kg_mol
        h2o_produced_kg = volume * Person.INTERNAL_H2O_SATURATION_DENSITY

        masses_inhaled[air.O2_INDEX] *= Person.PROPORTION_OF_O2_EXHALED
        masses_inhaled[air.CO2_INDEX] += co2_produced_kg
        masses_inhaled[air.H2O_INDEX] += h2o_produced_kg

        self.lung_composition += masses_inhaled
        dt_remaining = dt - dt_used

        if dt_remaining > 0:
            self._update_exhale_rate()
            self._time_elapsed_in_breathing_state = 0
            self._breathing_state += 1
            self._exhale(dt_remaining)

    def _exhale(self, dt: float = 0.0333):
        """
        exhale helper function
        :param dt: time step
        """
        dt_used = min(Person.BREATHING_CYCLE[self._breathing_state] - self._time_elapsed_in_breathing_state, dt)
        self._time_elapsed_in_breathing_state += dt_used
        masses_exhaled = self.exhale_rate * dt_used
        self.lung_composition -= masses_exhaled
        self.room.add_gas(masses_exhaled, mode='mass')

        dt_remaining = dt - dt_used

        if dt_remaining > 0:
            self._time_elapsed_in_breathing_state = 0
            self._breathing_state += 1
            self._pause(dt_remaining)

    def _pause(self, dt: float = 0.0333):
        """
        pause helper function
        :param dt: time step
        """
        dt_used = min(Person.BREATHING_CYCLE[self._breathing_state] - self._time_elapsed_in_breathing_state, dt)
        self._time_elapsed_in_breathing_state += dt_used
        dt_remaining = dt - dt_used
        if dt_remaining > 0:
            self._time_elapsed_in_breathing_state = 0
            self._breathing_state = 0
            self._inhale(dt_remaining)

    def _update_exhale_rate(self):
        self._exhale_rate = self.lung_composition / Person.EXHALE_DURATION

    def _is_air_safe(self):
        pressures = self.room.get_pressures()
        total_pressure = np.sum(pressures)
        return (pressures[air.CO2_INDEX] <= 5999.51 and
                7999.34 <= pressures[air.O2_INDEX] <= 160000 and
                6266.15 <= total_pressure <= 3039000)

