from typing import Optional


def moving_average(buffer: list[float], window_size: int) -> Optional[float]:
    """
    Retorna a média das últimas 'window_size' amostras do buffer.
    Se o buffer estiver vazio, retorna None.
    """
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
    """
    Filtro IIR de 1ª ordem (suavização exponencial):
    y[n] = alpha * x[n] + (1 - alpha) * y[n-1]

    Se prev_y for None, consideramos y[0] = x[0].
    """
    if not (0.0 < alpha <= 1.0):
        raise ValueError("alpha deve estar em (0, 1].")

    if prev_y is None:
        return x

    return alpha * x + (1.0 - alpha) * prev_y
