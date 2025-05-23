from subsystem import Subsystem  # Assuming this is in a file named subsystem.py
from power_source import PowerSource  # Assuming this is in a file named power_source.py
from typing import Union, List, Dict, Tuple, Any


class Light(Subsystem):
    # Data structure for crop-specific light requirements
    # Key: crop name (lowercase string)
    # Value: dict with "PPFD" (Photosynthetic Photon Flux Density in umol/m^2/s)
    #          and "POWER_W_M2" (Electrical power in W/m^2 to achieve that PPFD)
    CROP_LIGHT_REQUIREMENTS: Dict[str, Dict[str, float]] = {
        "potato": {"PPFD": 700, "POWER_W_M2": 300},
        "quinoa": {"PPFD": 600, "POWER_W_M2": 250},
        "beans": {"PPFD": 600, "POWER_W_M2": 250},  # e.g., common beans, soybeans
        "spinach": {"PPFD": 400, "POWER_W_M2": 200},
        "kale": {"PPFD": 400, "POWER_W_M2": 200},
        "blackberries": {"PPFD": 700, "POWER_W_M2": 350},
        "strawberries": {"PPFD": 600, "POWER_W_M2": 300},
        "lettuce": {"PPFD": 300, "POWER_W_M2": 150},  # Added example
        "tomato": {"PPFD": 800, "POWER_W_M2": 380},  # Added example (fruiting stage)
        "peppers": {"PPFD": 750, "POWER_W_M2": 360},  # Added example
        "default": {"PPFD": 500, "POWER_W_M2": 250}  # A default fallback
    }

    def __init__(self,
                 name: str,
                 source: PowerSource,
                 area_m2: float,
                 target_crops: Union[str, List[str]],
                 brightness_percent: float = 100.0):
        """
        Initializes the Light subsystem.

        :param name: Name of the light system.
        :param source: Power source object.
        :param area_m2: The total area to be illuminated in square meters.
        :param target_crops: A single crop name (str) or a list of crop names (List[str])
                             that this light system is intended for.
        :param brightness_percent: The operational brightness of the light, as a percentage (0-100).
                                   Defaults to 100%.
        """
        super().__init__(name, source)

        if area_m2 <= 0:
            raise ValueError("Illuminated area (area_m2) must be positive.")
        self.area_m2 = area_m2

        if not target_crops:
            raise ValueError("target_crops cannot be empty. Please specify at least one crop or 'default'.")

        if isinstance(target_crops, str):
            self.target_crops = [target_crops.lower()]
        elif isinstance(target_crops, list):
            self.target_crops = [crop.lower() for crop in target_crops]
        else:
            raise TypeError("target_crops must be a string or a list of strings.")

        if not (0 <= brightness_percent <= 100):
            raise ValueError("brightness_percent must be between 0 and 100.")
        self.brightness_percent = brightness_percent

        self.target_operational_ppfd_umol_m2_s: float = 0.0
        self.base_operational_power_w_m2: float = 0.0

        self._configure_for_crops()

        # Current actual PPFD based on brightness
        self.current_target_ppfd_umol_m2_s = self.target_operational_ppfd_umol_m2_s * (self.brightness_percent / 100.0)

        # Total electrical power draw for the entire area at current brightness
        self._electrical_power_draw_w = self.base_operational_power_w_m2 * self.area_m2 * (
                    self.brightness_percent / 100.0)

    def _configure_for_crops(self):
        """
        Determines the operational PPFD and Power/m^2 based on the target_crops list.
        It will select the maximum PPFD required by any listed crop and the
        corresponding power density (or max power density if multiple crops share max PPFD).
        """
        max_ppfd_found = 0.0
        power_for_max_ppfd = 0.0

        found_valid_crop = False
        for crop_name in self.target_crops:
            crop_data = self.CROP_LIGHT_REQUIREMENTS.get(crop_name)
            if not crop_data:
                print(
                    f"Warning: Crop '{crop_name}' not found in CROP_LIGHT_REQUIREMENTS. Using 'default' if available or skipping.")
                if not self.target_crops:  # If this was the only crop and it's not found
                    crop_data = self.CROP_LIGHT_REQUIREMENTS.get("default")
                    if not crop_data:
                        raise ValueError(f"Crop '{crop_name}' not found and no 'default' crop defined.")
                else:  # If other crops exist, or if default will be picked up later
                    continue

            found_valid_crop = True
            current_crop_ppfd = crop_data["PPFD"]
            current_crop_power_w_m2 = crop_data["POWER_W_M2"]

            if current_crop_ppfd > max_ppfd_found:
                max_ppfd_found = current_crop_ppfd
                power_for_max_ppfd = current_crop_power_w_m2
            elif current_crop_ppfd == max_ppfd_found:
                # If PPFD is the same, choose the one with higher power requirement (more conservative)
                power_for_max_ppfd = max(power_for_max_ppfd, current_crop_power_w_m2)

        if not found_valid_crop:  # If all specified crops were invalid and no default was applicable earlier
            default_data = self.CROP_LIGHT_REQUIREMENTS.get("default")
            if default_data:
                print("Warning: No valid target crops found from input list. Using 'default' settings.")
                max_ppfd_found = default_data["PPFD"]
                power_for_max_ppfd = default_data["POWER_W_M2"]
            else:
                raise ValueError("No valid crops specified and no 'default' configuration available.")

        self.target_operational_ppfd_umol_m2_s = max_ppfd_found
        self.base_operational_power_w_m2 = power_for_max_ppfd

        if self.target_operational_ppfd_umol_m2_s == 0 and self.base_operational_power_w_m2 == 0 and self.target_crops != [
            'default']:
            print(
                f"Warning: Light system '{self.name}' configured with 0 PPFD and 0 Power/m^2 based on crops: {self.target_crops}. This might be due to missing crop data or all target crops having 0 requirements.")

    def __repr__(self):
        return (f"Light(name='{self.name}', area={self.area_m2}m^2, "
                f"crops={self.target_crops}, brightness={self.brightness_percent}%, "
                f"target_PPFD={self.current_target_ppfd_umol_m2_s:.0f} umol/m^2/s, "
                f"power_draw={self._electrical_power_draw_w:.2f}W)")

    def update(self, dt: float = 0.0333) -> float:
        """
        Updates the light system, consumes power, and calculates heat produced.
        Assumes all electrical energy consumed by the light system is eventually
        converted to heat in the environment.

        :param dt: Time step duration in seconds.
        :return: Heat produced by the subsystem in Joules during this time step.
        """
        if self._electrical_power_draw_w <= 0:
            return 0.0  # No power draw, no heat

        # The PowerSource.consume_electricity method expects power (Watts) and dt,
        # and returns the actual energy consumed in Joules.
        # Or, if mode="energy", it expects energy (Joules).
        # Original Light class called it with energy: self.power_source.consume_electricity(self._power * dt)
        # Let's stick to that pattern for PowerSource.

        requested_energy_j = self._electrical_power_draw_w * dt
        actual_energy_consumed_j = self.power_source.consume_electricity(requested_energy_j, mode="energy")

        # Assuming all electrical energy consumed by the light fixture becomes heat in the system.
        # A more detailed model could split this into light energy and heat based on PAR efficiency.
        heat_produced_j = actual_energy_consumed_j

        return heat_produced_j

    # --- Getter methods ---
    def get_target_crops(self) -> List[str]:
        return self.target_crops

    def get_illuminated_area_m2(self) -> float:
        return self.area_m2

    def get_brightness_percent(self) -> float:
        return self.brightness_percent

    def get_target_operational_ppfd(self) -> float:
        """Returns the PPFD the light system aims for at 100% brightness for the configured crops."""
        return self.target_operational_ppfd_umol_m2_s

    def get_current_target_ppfd(self) -> float:
        """Returns the current operational PPFD considering the brightness setting."""
        return self.current_target_ppfd_umol_m2_s

    def get_electrical_power_draw_w(self) -> float:
        """Returns the current total electrical power draw in Watts."""
        return self._electrical_power_draw_w

    def set_brightness_percent(self, brightness_percent: float):
        """
        Sets the brightness of the light system.

        :param brightness_percent: New brightness level (0-100).
        """
        if not (0 <= brightness_percent <= 100):
            raise ValueError("brightness_percent must be between 0 and 100.")
        self.brightness_percent = brightness_percent

        # Recalculate current PPFD and power draw
        self.current_target_ppfd_umol_m2_s = self.target_operational_ppfd_umol_m2_s * (self.brightness_percent / 100.0)
        self._electrical_power_draw_w = self.base_operational_power_w_m2 * self.area_m2 * (
                    self.brightness_percent / 100.0)
        print(f"Light '{self.name}' brightness set to {self.brightness_percent}%. "
              f"New PPFD: {self.current_target_ppfd_umol_m2_s:.0f} umol/m^2/s, "
              f"New Power Draw: {self._electrical_power_draw_w:.2f}W")
