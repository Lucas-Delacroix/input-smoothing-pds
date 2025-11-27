from typing import Optional


def moving_average(buffer: list[float], window_size: int) -> Optional[float]:
    if not buffer:
        return None

    if window_size <= 0:
        raise ValueError("window_size deve ser > 0")

    effective_size = min(len(buffer), window_size)
    window = buffer[-effective_size:]
    return sum(window) / effective_size


def exp_smoothing(x: float,
                  prev_y: Optional[float],
                  alpha: float) -> float:
    if not (0.0 < alpha <= 1.0):
        raise ValueError("alpha deve estar em (0, 1].")

    if prev_y is None:
        return x

    return alpha * x + (1.0 - alpha) * prev_y
