class Light:
    def __init__(self, size, brightness, power_per_size_per_lumen):
        self.brightness = brightness
        self.size = size
        self.power_rate = size * power_per_size_per_lumen * brightness
