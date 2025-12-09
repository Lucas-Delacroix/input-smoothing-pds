from typing import Callable, Dict, Optional, Tuple
import time
import os

import pygame

from config import (
    ALPHA_STEP,
    BACKGROUND_COLOR,
    HUD_FONT,
    HUD_FONT_SIZE,
    HUD_LINE_HEIGHT,
    HUD_MARGIN_X,
    HUD_MARGIN_Y,
    HUD_TEXT_COLOR,
    MARKER_RADIUS,
    PARAM_CHANGE_COLOR,
    PARAM_CHANGE_INDICATOR_DURATION,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from filter_metadata import FILTERS, KEY_TO_FILTER_ID
from input_device import InputSmoother, Point
from ui_state import (
    MetricsTracker,
    ParamChangeIndicator,
    ViewTransform,
    VisibilityState,
)
from plot_3d import generate_3d_plot, generate_3d_surface_map




def create_window(fullscreen: bool = False) -> Tuple[pygame.Surface, bool]:
    pygame.display.set_caption(TITLE)
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return screen, True
    else:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        return screen, False


def build_font() -> pygame.font.Font:
    return pygame.font.SysFont(HUD_FONT, HUD_FONT_SIZE)


def handle_events(
    smoother: InputSmoother,
    history_enabled: bool,
    view_transform: ViewTransform,
    visibility: VisibilityState,
    param_indicator: ParamChangeIndicator,
    fullscreen: bool,
) -> Tuple[bool, bool, bool, bool, Optional[str], bool]:
    reset_requested = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, history_enabled, fullscreen, False, None, reset_requested

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False, history_enabled, fullscreen, False, None, reset_requested
            if event.key == pygame.K_SPACE and (event.mod & pygame.KMOD_CTRL):
                return True, history_enabled, fullscreen, False, "tremor", reset_requested
            if event.key == pygame.K_d and (event.mod & pygame.KMOD_CTRL):
                return True, history_enabled, fullscreen, False, "drift", reset_requested
            if event.key == pygame.K_r:
                reset_requested = True
                continue
            result = _handle_key(
                event.key, smoother, history_enabled, view_transform,
                visibility, param_indicator, fullscreen
            )
            if result is not None:
                history_enabled, fullscreen, generate_3d = result
                if generate_3d:
                    return True, history_enabled, fullscreen, True, None, reset_requested


    return True, history_enabled, fullscreen, False, None, reset_requested


def _handle_key(
    key: int,
    smoother: InputSmoother,
    history_enabled: bool,
    view_transform: ViewTransform,
    visibility: VisibilityState,
    param_indicator: ParamChangeIndicator,
    fullscreen: bool,
) -> Optional[Tuple[bool, bool, bool]]:
    key_actions: dict[int, Callable[[InputSmoother], None]] = {
        pygame.K_UP: lambda sm: sm.change_window(1),
        pygame.K_DOWN: lambda sm: sm.change_window(-1),
        pygame.K_RIGHT: lambda sm: sm.change_alpha(ALPHA_STEP),
        pygame.K_LEFT: lambda sm: sm.change_alpha(-ALPHA_STEP),
    }

    action = key_actions.get(key)
    if action:
        action(smoother)
        param_indicator.trigger(PARAM_CHANGE_INDICATOR_DURATION)
        return None

    if key == pygame.K_h:
        if history_enabled:
            smoother.clear_history()
        return (not history_enabled, fullscreen, False)

    filter_id = KEY_TO_FILTER_ID.get(key)
    if filter_id is not None:
        current = visibility.is_visible(filter_id)
        visibility.set_visible(filter_id, not current)
        return None

    if key == pygame.K_F11:
        return (history_enabled, not fullscreen, False)


    if key == pygame.K_g:
        return (history_enabled, fullscreen, True)

    return None


def _draw_traces(
    screen: pygame.Surface,
    smoother: InputSmoother,
    transform: ViewTransform,
    visibility: VisibilityState,
) -> None:
    for descriptor in FILTERS:
        if not visibility.is_visible(descriptor.id):
            continue

        trace = getattr(smoother, descriptor.trace_attr, None)
        if trace is None or len(trace) <= 1:
            continue

        points = trace.as_int_tuples()
        pygame.draw.lines(
            screen,
            descriptor.color,
            False,
            points,
            descriptor.line_width,
        )


def _draw_markers(
    screen: pygame.Surface,
    points_by_filter: Dict[str, Optional[Point]],
    transform: ViewTransform,
    visibility: VisibilityState,
) -> None:
    for descriptor in FILTERS:
        if not visibility.is_visible(descriptor.id):
            continue
        point = points_by_filter.get(descriptor.id)
        if point is None:
            continue
        x, y = point.as_int_tuple()
        pygame.draw.circle(screen, descriptor.cursor_color, (x, y), MARKER_RADIUS)




def _draw_param_change_indicator(
    screen: pygame.Surface,
    font: pygame.font.Font,
    indicator: ParamChangeIndicator,
) -> None:
    if indicator.active:
        alpha = min(255, int(255 * (indicator.timer / PARAM_CHANGE_INDICATOR_DURATION)))
        color = (*PARAM_CHANGE_COLOR, alpha)
        
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((255, 255, 0, alpha // 4))
        screen.blit(overlay, (0, 0))

        text = "PARÂMETRO ALTERADO!"
        text_surf = font.render(text, True, PARAM_CHANGE_COLOR)
        text_rect = text_surf.get_rect(center=(screen.get_width() // 2, 50))
        screen.blit(text_surf, text_rect)


def _draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    smoother: InputSmoother,
    history_enabled: bool,
    visibility: VisibilityState,
    transform: ViewTransform,
    fullscreen: bool,
    tremor_sim,
    drift_sim,
) -> None:
    lines = [
        f"N (moving_average): {smoother.window_size}",
        f"IIR alpha (exp.smooth): {smoother.alpha:.2f}",
        f"Histórico (H): {'ON' if history_enabled else 'OFF'}",
        f"Tremor: {'ON' if tremor_sim.enabled else 'OFF'} "
        f"(Int: {tremor_sim.intensity:.1f}, Freq: {tremor_sim.frequency:.1f}Hz)",
        f"Drift artificial: {'ON' if drift_sim.enabled else 'OFF'} "
        f"({drift_sim.pixels_per_second:.1f}px/s, Dir: {drift_sim.direction_deg:.0f}°)",
        f"Visibilidade:",
    ]

    for descriptor in FILTERS:
        visible = visibility.is_visible(descriptor.id)
        status = "ON" if visible else "OFF"
        lines.append(
            f"  {descriptor.name} ({descriptor.key_hint}): {status}"
        )

    toggle_keys = ", ".join(f.key_hint for f in FILTERS)

    lines.extend(
        [
            "",
            "Controles:",
            "  UP / DOWN    -> aumenta/diminui N",
            "  RIGHT / LEFT -> aumenta/diminui IIR alpha",
            "  H            -> liga/desliga histórico",
            f"  {toggle_keys:<12} -> toggle visibilidade",
            "  R            -> reset global (filtros, histórico, tremor e drift)",
            "  F11          -> tela cheia",
            "  G            -> gerar gráfico 3D",
            "  CTRL+SPACE   -> configurar tremor",
            "  CTRL+D       -> configurar drift",
            "  ESC          -> sair",
        ]
    )

    x, y = HUD_MARGIN_X, HUD_MARGIN_Y
    for line in lines:
        if line:
            surf = font.render(line, True, HUD_TEXT_COLOR)
            screen.blit(surf, (x, y))
        y += HUD_LINE_HEIGHT


def render_frame(
    screen: pygame.Surface,
    font: pygame.font.Font,
    smoother: InputSmoother,
    history_enabled: bool,
    raw_point: Point,
    ma_point: Optional[Point],
    exp_point: Point,
    drift_point: Optional[Point],
    transform: ViewTransform,
    visibility: VisibilityState,
    metrics: MetricsTracker,
    param_indicator: ParamChangeIndicator,
    fullscreen: bool,
    tremor_sim,
    drift_sim,
    tremor_modal=None,
) -> None:
    screen.fill(BACKGROUND_COLOR)
    
    if history_enabled:
        _draw_traces(screen, smoother, transform, visibility)

    points_by_filter: Dict[str, Optional[Point]] = {
        "raw": raw_point,
        "ma": ma_point,
        "exp": exp_point,
        "drift": drift_point,
    }

    _draw_markers(screen, points_by_filter, transform, visibility)
    _draw_hud(screen, font, smoother, history_enabled, visibility, transform, fullscreen, tremor_sim, drift_sim)
    _draw_param_change_indicator(screen, font, param_indicator)
    
    if tremor_modal:
        tremor_modal.render(screen)
    
    pygame.display.flip()


def generate_3d_visualization(smoother: InputSmoother) -> None:
    timestamp = int(time.time())
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    plot_path = os.path.join(output_dir, f"plot_3d_{timestamp}.png")
    map_path = os.path.join(output_dir, f"map_3d_{timestamp}.png")
    
    try:
        generate_3d_plot(smoother, plot_path)
        generate_3d_surface_map(smoother, map_path)
        print(f"Gráficos 3D gerados em: {output_dir}/")
    except Exception as e:
        print(f"Erro ao gerar gráficos 3D: {e}")
