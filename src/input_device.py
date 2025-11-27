from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from filters import exp_smoothing, moving_average


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def as_int_tuple(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


class TraceBuffer:
    def __init__(self, max_size: int):
        self._points: Deque[Point] = deque(maxlen=max_size)

    def append(self, point: Point) -> None:
        self._points.append(point)

    def as_int_tuples(self) -> list[tuple[int, int]]:
        return [point.as_int_tuple() for point in self._points]

    def latest(self) -> Optional[Point]:
        return self._points[-1] if self._points else None

    def __len__(self) -> int:
        return len(self._points)

    def __iter__(self):
        return iter(self._points)


class InputSmoother:
    def __init__(
        self,
        buffer_size: int,
        window_size: int,
        alpha: float,
        min_window: int,
        min_alpha: float,
        max_alpha: float,
    ):
        self._window_size = max(min_window, window_size)
        self._alpha = self._clamp(alpha, min_alpha, max_alpha)
        self._min_window = min_window
        self._min_alpha = min_alpha
        self._max_alpha = max_alpha

        self.raw_trace = TraceBuffer(buffer_size)
        self.moving_average_trace = TraceBuffer(buffer_size)
        self.exp_trace = TraceBuffer(buffer_size)

        self._exp_point: Optional[Point] = None

    def add_sample(self, x: float, y: float) -> tuple[Point, Optional[Point], Point]:
        point = Point(x, y)
        self.raw_trace.append(point)

        ma_point = self._append_moving_average()
        exp_point = self._append_exponential(point)

        return point, ma_point, exp_point

    def _append_moving_average(self) -> Optional[Point]:
        ma_x = moving_average([p.x for p in self.raw_trace], self._window_size)
        ma_y = moving_average([p.y for p in self.raw_trace], self._window_size)

        if ma_x is None or ma_y is None:
            return None

        ma_point = Point(ma_x, ma_y)
        self.moving_average_trace.append(ma_point)
        return ma_point

    def _append_exponential(self, point: Point) -> Point:
        prev_x = self._exp_point.x if self._exp_point else None
        prev_y = self._exp_point.y if self._exp_point else None

        self._exp_point = Point(
            exp_smoothing(point.x, prev_x, self._alpha),
            exp_smoothing(point.y, prev_y, self._alpha),
        )

        self.exp_trace.append(self._exp_point)
        return self._exp_point

    def change_window(self, delta: int) -> None:
        self._window_size = max(self._min_window, self._window_size + delta)

    def change_alpha(self, delta: float) -> None:
        self._alpha = self._clamp(self._alpha + delta, self._min_alpha, self._max_alpha)

    @property
    def window_size(self) -> int:
        return self._window_size

    @property
    def alpha(self) -> float:
        return self._alpha

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(value, max_value))
