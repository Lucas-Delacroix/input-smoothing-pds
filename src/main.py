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
)
from input_device import InputSmoother
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

    # Estado da UI
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

        # Processa eventos
        running, history_enabled, fullscreen, generate_3d = handle_events(
            smoother,
            history_enabled,
            view_transform,
            visibility,
            param_indicator,
            fullscreen,
        )

        if not running:
            break

        # Atualiza tela cheia se necessário
        is_currently_fullscreen = bool(screen.get_flags() & pygame.FULLSCREEN)
        if fullscreen != is_currently_fullscreen:
            screen, fullscreen = create_window(fullscreen)

        # Gera gráfico 3D se solicitado
        if generate_3d:
            generate_3d_visualization(smoother)

        # Atualiza indicador de mudança
        param_indicator.update(dt_ms)

        # Captura posição do mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        raw_point, ma_point, exp_point = smoother.add_sample(
            mouse_x,
            mouse_y,
            store_history=history_enabled,
        )

        # Atualiza métricas
        current_fps = clock.get_fps()
        if current_fps > 0:
            metrics.add_fps(current_fps)
        metrics.add_latency(dt_ms)

        # Renderiza frame
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
        )

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
