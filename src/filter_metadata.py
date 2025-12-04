from dataclasses import dataclass
from typing import List, Tuple

import pygame

from config import (
    RAW_COLOR,
    MOVING_AVERAGE_COLOR,
    EXP_COLOR,
    DRIFT_CORRECTED_COLOR,
    CURSOR_RAW_COLOR,
    CURSOR_MA_COLOR,
    CURSOR_EXP_COLOR,
    CURSOR_DRIFT_COLOR,
    RAW_LINE_WIDTH,
    SMOOTH_LINE_WIDTH,
    DEFAULT_RAW_VISIBLE,
    DEFAULT_MA_VISIBLE,
    DEFAULT_EXP_VISIBLE,
    DEFAULT_DRIFT_VISIBLE,
)


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class FilterDescriptor:
    id: str
    name: str
    trace_attr: str
    key: int
    key_hint: str
    visibility_default: bool
    color: Color
    cursor_color: Color
    line_width: int
    mpl_color: str
    density_cmap: str


FILTERS: List[FilterDescriptor] = [
    FilterDescriptor(
        id="raw",
        name="Raw",
        trace_attr="raw_trace",
        key=pygame.K_1,
        key_hint="1",
        visibility_default=DEFAULT_RAW_VISIBLE,
        color=RAW_COLOR,
        cursor_color=CURSOR_RAW_COLOR,
        line_width=RAW_LINE_WIDTH,
        mpl_color="red",
        density_cmap="Reds",
    ),
    FilterDescriptor(
        id="ma",
        name="MA",
        trace_attr="moving_average_trace",
        key=pygame.K_2,
        key_hint="2",
        visibility_default=DEFAULT_MA_VISIBLE,
        color=MOVING_AVERAGE_COLOR,
        cursor_color=CURSOR_MA_COLOR,
        line_width=SMOOTH_LINE_WIDTH,
        mpl_color="green",
        density_cmap="Greens",
    ),
    FilterDescriptor(
        id="exp",
        name="Exp",
        trace_attr="exp_trace",
        key=pygame.K_3,
        key_hint="3",
        visibility_default=DEFAULT_EXP_VISIBLE,
        color=EXP_COLOR,
        cursor_color=CURSOR_EXP_COLOR,
        line_width=SMOOTH_LINE_WIDTH,
        mpl_color="blue",
        density_cmap="Blues",
    ),
    FilterDescriptor(
        id="drift",
        name="Drift corr.",
        trace_attr="drift_corrected_trace",
        key=pygame.K_4,
        key_hint="4",
        visibility_default=DEFAULT_DRIFT_VISIBLE,
        color=DRIFT_CORRECTED_COLOR,
        cursor_color=CURSOR_DRIFT_COLOR,
        line_width=SMOOTH_LINE_WIDTH,
        mpl_color="gold",
        density_cmap="YlOrBr",
    ),
]


KEY_TO_FILTER_ID = {f.key: f.id for f in FILTERS}

