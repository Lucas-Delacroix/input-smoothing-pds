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

