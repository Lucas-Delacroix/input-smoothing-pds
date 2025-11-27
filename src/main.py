import sys

import pygame

from config import (
    ALPHA_MAX,
    ALPHA_MIN,
    DEFAULT_HISTORY_ENABLED,
    DEFAULT_IIR_ALPHA,
    DEFAULT_MOVING_AVERAGE_WINDOW,
    FPS,
    MAX_BUFFER,
    MOVING_AVERAGE_MIN,
)
from input_device import InputSmoother
from ui import build_font, create_window, handle_events, render_frame


def main() -> None:
    pygame.init()
    screen = create_window()
    clock = pygame.time.Clock()
    font = build_font()

    smoother = InputSmoother(
        buffer_size=MAX_BUFFER,
        window_size=DEFAULT_MOVING_AVERAGE_WINDOW,
        alpha=DEFAULT_IIR_ALPHA,
        min_window=MOVING_AVERAGE_MIN,
        min_alpha=ALPHA_MIN,
        max_alpha=ALPHA_MAX,
    )

    history_enabled = DEFAULT_HISTORY_ENABLED
    running = True
    while running:
        running, history_enabled = handle_events(smoother, history_enabled)
        if not running:
            break

        mouse_x, mouse_y = pygame.mouse.get_pos()
        raw_point, ma_point, exp_point = smoother.add_sample(
            mouse_x,
            mouse_y,
            store_history=history_enabled,
        )

        render_frame(
            screen,
            font,
            smoother,
            history_enabled,
            raw_point,
            ma_point,
            exp_point,
        )
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
