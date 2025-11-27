import sys
import time

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
    PARAM_CHANGE_INDICATOR_DURATION,
    TREMOR_ENABLED,
    TREMOR_INTENSITY,
    TREMOR_FREQUENCY,
)
from input_device import InputSmoother
from tremor_simulator import TremorSimulator
from tremor_modal import TremorModal
from ui import (
    build_font,
    create_window,
    handle_events,
    render_frame,
    generate_3d_visualization,
)
from ui_state import (
    MetricsTracker,
    ParamChangeIndicator,
    ViewTransform,
    VisibilityState,
)


def main() -> None:
    pygame.init()
    screen, fullscreen = create_window()
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

    tremor_sim = TremorSimulator(
        enabled=TREMOR_ENABLED,
        intensity=TREMOR_INTENSITY,
        frequency=TREMOR_FREQUENCY,
    )

    tremor_modal = TremorModal(tremor_sim, font)

    history_enabled = DEFAULT_HISTORY_ENABLED
    view_transform = ViewTransform()
    visibility = VisibilityState()
    metrics = MetricsTracker()
    param_indicator = ParamChangeIndicator()

    running = True
    last_time = time.time()
    
    while running:
        frame_start = time.time()
        dt_ms = int((frame_start - last_time) * 1000)
        last_time = frame_start

        if tremor_modal.active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    tremor_modal.handle_key(event.key, event.mod)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    tremor_modal.handle_mouse(event.pos, event.button, True)
                if event.type == pygame.MOUSEBUTTONUP:
                    tremor_modal.handle_mouse(event.pos, event.button, False)
                if event.type == pygame.MOUSEMOTION:
                    if tremor_modal.slider_dragging:
                        tremor_modal.handle_mouse(event.pos, 0, True)
        else:
            running, history_enabled, fullscreen, generate_3d, open_modal = handle_events(
                smoother,
                history_enabled,
                view_transform,
                visibility,
                param_indicator,
                fullscreen,
            )

            if open_modal:
                tremor_modal.open()

            if not running:
                break

        is_currently_fullscreen = bool(screen.get_flags() & pygame.FULLSCREEN)
        if fullscreen != is_currently_fullscreen:
            screen, fullscreen = create_window(fullscreen)

        if generate_3d:
            generate_3d_visualization(smoother)

        param_indicator.update(dt_ms)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x, mouse_y = tremor_sim.apply_tremor(mouse_x, mouse_y)
        
        raw_point, ma_point, exp_point = smoother.add_sample(
            mouse_x,
            mouse_y,
            store_history=history_enabled,
        )

        current_fps = clock.get_fps()
        if current_fps > 0:
            metrics.add_fps(current_fps)
        metrics.add_latency(dt_ms)

        render_frame(
            screen,
            font,
            smoother,
            history_enabled,
            raw_point,
            ma_point,
            exp_point,
            view_transform,
            visibility,
            metrics,
            param_indicator,
            fullscreen,
            tremor_sim,
            tremor_modal,
        )

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
