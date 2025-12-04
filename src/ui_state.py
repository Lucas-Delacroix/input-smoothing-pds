from dataclasses import dataclass
from collections import deque
from typing import Deque, Dict

from config import (
    ZOOM_DEFAULT,
    ZOOM_MIN,
    ZOOM_MAX,
    METRICS_HISTORY_SIZE,
)
from filter_metadata import FILTERS


@dataclass
class ViewTransform:
    zoom: float = ZOOM_DEFAULT
    target_zoom: float = ZOOM_DEFAULT
    pan_x: float = 0.0
    pan_y: float = 0.0

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (x * self.zoom + self.pan_x, y * self.zoom + self.pan_y)

    def reset(self) -> None:
        self.zoom = ZOOM_DEFAULT
        self.target_zoom = ZOOM_DEFAULT
        self.pan_x = 0.0
        self.pan_y = 0.0

    def update_smooth(self, factor: float) -> None:
        diff = self.target_zoom - self.zoom
        self.zoom += diff * factor
        if abs(diff) < 0.001:
            self.zoom = self.target_zoom


class VisibilityState:
    def __init__(self) -> None:
        self._filters: Dict[str, bool] = {
            f.id: f.visibility_default for f in FILTERS
        }

    def is_visible(self, filter_id: str) -> bool:
        return self._filters.get(filter_id, True)

    def set_visible(self, filter_id: str, visible: bool) -> None:
        self._filters[filter_id] = visible


@dataclass
class MetricsTracker:
    fps_history: Deque[float]
    latency_history: Deque[float]

    def __init__(self, history_size: int = METRICS_HISTORY_SIZE):
        self.fps_history = deque(maxlen=history_size)
        self.latency_history = deque(maxlen=history_size)

    def add_fps(self, fps: float) -> None:
        self.fps_history.append(fps)

    def add_latency(self, latency_ms: float) -> None:
        self.latency_history.append(latency_ms)

    def get_avg_fps(self) -> float:
        if not self.fps_history:
            return 0.0
        return sum(self.fps_history) / len(self.fps_history)

    def get_avg_latency(self) -> float:
        if not self.latency_history:
            return 0.0
        return sum(self.latency_history) / len(self.latency_history)


@dataclass
class ParamChangeIndicator:
    active: bool = False
    timer: int = 0

    def trigger(self, duration_ms: int) -> None:
        self.active = True
        self.timer = duration_ms

    def update(self, dt_ms: int) -> None:
        if self.active:
            self.timer -= dt_ms
            if self.timer <= 0:
                self.active = False
                self.timer = 0
