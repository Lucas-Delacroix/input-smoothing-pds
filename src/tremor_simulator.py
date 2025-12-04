import math
import time
from typing import Tuple

import numpy as np


class TremorSimulator:
    def __init__(
        self,
        enabled: bool = False,
        intensity: float = 5.0,
        frequency: float = 10.0,
    ):
        self.enabled = enabled
        self.intensity = intensity
        self.frequency = frequency
        self.start_time = time.time()
        self._last_noise_x = 0.0
        self._last_noise_y = 0.0
        
    def apply_tremor(self, x: float, y: float) -> Tuple[float, float]:
        if not self.enabled:
            return x, y
        
        t = time.time() - self.start_time
        sin_x = math.sin(2 * math.pi * self.frequency * t) * (self.intensity * 0.3)
        sin_y = math.cos(2 * math.pi * self.frequency * t * 1.1) * (self.intensity * 0.3)
        
        noise_x = np.random.normal(0, self.intensity * 0.7)
        noise_y = np.random.normal(0, self.intensity * 0.7)
        
        alpha = 0.3
        self._last_noise_x = alpha * noise_x + (1 - alpha) * self._last_noise_x
        self._last_noise_y = alpha * noise_y + (1 - alpha) * self._last_noise_y
        
        tremor_x = sin_x + self._last_noise_x
        tremor_y = sin_y + self._last_noise_y
        
        return x + tremor_x, y + tremor_y
    
    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            self.start_time = time.time()
    
    def set_intensity(self, intensity: float) -> None:
        self.intensity = max(0.0, intensity)
    
    def set_frequency(self, frequency: float) -> None:
        self.frequency = max(0.1, frequency)


class DriftSimulator:
    def __init__(
        self,
        enabled: bool = False,
        pixels_per_second: float = 25.0,
        direction_deg: float = 0.0,
    ):
        self.enabled = enabled
        self.pixels_per_second = max(0.0, pixels_per_second)
        self.direction_deg = direction_deg
        self._direction_rad = math.radians(direction_deg)
        self._last_update: float | None = None
        self._offset_x = 0.0
        self._offset_y = 0.0

    def apply_drift(self, x: float, y: float) -> Tuple[float, float]:
        if not self.enabled or self.pixels_per_second <= 0.0:
            self._reset_clock()
            self._offset_x = 0.0
            self._offset_y = 0.0
            return x, y

        now = time.time()
        if self._last_update is None:
            self._last_update = now
            return x + self._offset_x, y + self._offset_y

        elapsed = now - self._last_update
        self._last_update = now

        drift_x = math.cos(self._direction_rad) * self.pixels_per_second * elapsed
        drift_y = math.sin(self._direction_rad) * self.pixels_per_second * elapsed

        self._offset_x += drift_x
        self._offset_y += drift_y

        return x + self._offset_x, y + self._offset_y

    def get_offset(self) -> Tuple[float, float]:
        return self._offset_x, self._offset_y

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            self._reset_clock()
        else:
            self.reset()

    def set_speed(self, pixels_per_second: float) -> None:
        self.pixels_per_second = max(0.0, pixels_per_second)

    def set_direction(self, direction_deg: float) -> None:
        self.direction_deg = direction_deg % 360
        self._direction_rad = math.radians(self.direction_deg)
        self._reset_clock()

    def reset(self) -> None:
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._reset_clock()

    def _reset_clock(self) -> None:
        self._last_update = None
