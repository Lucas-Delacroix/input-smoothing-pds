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

    def clear(self) -> None:
        self._points.clear()

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
        drift_window: int,
    ):
        initial_window_size = max(min_window, window_size)
        initial_alpha = self._clamp(alpha, min_alpha, max_alpha)

        self._window_size = initial_window_size
        self._alpha = initial_alpha
        self._min_window = min_window
        self._min_alpha = min_alpha
        self._max_alpha = max_alpha
        self._drift_window = max(1, drift_window)

        self._default_window_size = initial_window_size
        self._default_alpha = initial_alpha

        self._sample_buffer: Deque[Point] = deque(maxlen=buffer_size)
        self.raw_trace = TraceBuffer(buffer_size)
        self.moving_average_trace = TraceBuffer(buffer_size)
        self.exp_trace = TraceBuffer(buffer_size)
        self.drift_corrected_trace = TraceBuffer(buffer_size)

        self._exp_point: Optional[Point] = None

    def add_sample(
        self,
        x: float,
        y: float,
        store_history: bool = True,
        drift_offset: Optional[tuple[float, float]] = None,
    ) -> tuple[Point, Optional[Point], Point, Optional[Point]]:
        point = Point(x, y)
        self._sample_buffer.append(point)

        ma_point = self._compute_moving_average()
        exp_point = self._compute_exponential(point)
        drift_point = self._compute_drift_corrected(point, drift_offset)

        if store_history:
            self.raw_trace.append(point)
            if ma_point is not None:
                self.moving_average_trace.append(ma_point)
            self.exp_trace.append(exp_point)
            if drift_point is not None:
                self.drift_corrected_trace.append(drift_point)

        return point, ma_point, exp_point, drift_point

    def _compute_moving_average(self) -> Optional[Point]:
        if not self._sample_buffer:
            return None

        sample_x = [p.x for p in self._sample_buffer]
        sample_y = [p.y for p in self._sample_buffer]
        ma_x = moving_average(sample_x, self._window_size)
        ma_y = moving_average(sample_y, self._window_size)

        if ma_x is None or ma_y is None:
            return None

        ma_point = Point(ma_x, ma_y)
        return ma_point

    def _compute_exponential(self, point: Point) -> Point:
        prev_x = self._exp_point.x if self._exp_point else None
        prev_y = self._exp_point.y if self._exp_point else None

        self._exp_point = Point(
            exp_smoothing(point.x, prev_x, self._alpha),
            exp_smoothing(point.y, prev_y, self._alpha),
        )

        return self._exp_point

    def _compute_drift_corrected(
        self,
        point: Point,
        drift_offset: Optional[tuple[float, float]],
    ) -> Optional[Point]:
        if drift_offset is None:
            return None

        offset_x, offset_y = drift_offset
        return Point(point.x - offset_x, point.y - offset_y)

    def change_window(self, delta: int) -> None:
        self._window_size = max(self._min_window, self._window_size + delta)

    def change_alpha(self, delta: float) -> None:
        self._alpha = self._clamp(self._alpha + delta, self._min_alpha, self._max_alpha)

    def clear_history(self) -> None:
        self.raw_trace.clear()
        self.moving_average_trace.clear()
        self.exp_trace.clear()
        self._sample_buffer.clear()
        self._exp_point = None
        self.drift_corrected_trace.clear()

    def reset(self) -> None:
        self._window_size = self._default_window_size
        self._alpha = self._default_alpha
        self.clear_history()

    @property
    def window_size(self) -> int:
        return self._window_size

    @property
    def alpha(self) -> float:
        return self._alpha

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(value, max_value))
