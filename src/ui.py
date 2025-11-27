from typing import Callable, Optional, Tuple
import time
import os

import pygame

from config import (
    ALPHA_STEP,
    BACKGROUND_COLOR,
    CURSOR_EXP_COLOR,
    CURSOR_MA_COLOR,
    CURSOR_RAW_COLOR,
    EXP_COLOR,
    HUD_FONT,
    HUD_FONT_SIZE,
    HUD_LINE_HEIGHT,
    HUD_MARGIN_X,
    HUD_MARGIN_Y,
    HUD_TEXT_COLOR,
    MARKER_RADIUS,
    METRICS_GRAPH_HEIGHT,
    METRICS_GRAPH_WIDTH,
    METRICS_GRAPH_X,
    METRICS_GRAPH_Y,
    MOVING_AVERAGE_COLOR,
    PAN_SENSITIVITY,
    PARAM_CHANGE_COLOR,
    PARAM_CHANGE_INDICATOR_DURATION,
    RAW_COLOR,
    RAW_LINE_WIDTH,
    SMOOTH_LINE_WIDTH,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    ZOOM_MAX,
    ZOOM_MIN,
    ZOOM_STEP,
)
from input_device import InputSmoother, Point
from ui_state import (
    MetricsTracker,
    ParamChangeIndicator,
    ViewTransform,
    VisibilityState,
)
from plot_3d import generate_3d_plot, generate_3d_surface_map


_pan_dragging = False
_pan_start_pos = (0, 0)
_pan_start_transform = ViewTransform()


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
) -> Tuple[bool, bool, bool, bool]:
    global _pan_dragging, _pan_start_pos, _pan_start_transform

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, history_enabled, fullscreen, False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False, history_enabled, fullscreen, False
            result = _handle_key(
                event.key, smoother, history_enabled, view_transform,
                visibility, param_indicator, fullscreen
            )
            if result is not None:
                history_enabled, fullscreen, generate_3d = result
                if generate_3d:
                    return True, history_enabled, fullscreen, True

        if event.type == pygame.MOUSEWHEEL:
            zoom_delta = ZOOM_STEP * event.y
            new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, view_transform.zoom + zoom_delta))
            view_transform.zoom = new_zoom

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:
                _pan_dragging = True
                _pan_start_pos = event.pos
                _pan_start_transform.zoom = view_transform.zoom
                _pan_start_transform.pan_x = view_transform.pan_x
                _pan_start_transform.pan_y = view_transform.pan_y

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                _pan_dragging = False

        if event.type == pygame.MOUSEMOTION:
            if _pan_dragging:
                dx = (event.pos[0] - _pan_start_pos[0]) * PAN_SENSITIVITY
                dy = (event.pos[1] - _pan_start_pos[1]) * PAN_SENSITIVITY
                view_transform.pan_x = _pan_start_transform.pan_x + dx
                view_transform.pan_y = _pan_start_transform.pan_y + dy

    return True, history_enabled, fullscreen, False


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

    if key == pygame.K_1:
        visibility.raw_visible = not visibility.raw_visible
        return None
    if key == pygame.K_2:
        visibility.ma_visible = not visibility.ma_visible
        return None
    if key == pygame.K_3:
        visibility.exp_visible = not visibility.exp_visible
        return None

    if key == pygame.K_F11:
        return (history_enabled, not fullscreen, False)

    if key == pygame.K_r:
        view_transform.reset()
        return None

    if key == pygame.K_g:
        return (history_enabled, fullscreen, True)

    return None


def _apply_transform(point: Point, transform: ViewTransform, screen_width: int, screen_height: int) -> Tuple[int, int]:
    center_x = screen_width / 2
    center_y = screen_height / 2

    x = (point.x - center_x) * transform.zoom + center_x
    y = (point.y - center_y) * transform.zoom + center_y

    x += transform.pan_x
    y += transform.pan_y

    return int(x), int(y)


def _draw_traces(
    screen: pygame.Surface,
    smoother: InputSmoother,
    transform: ViewTransform,
    visibility: VisibilityState,
) -> None:
    screen_width, screen_height = screen.get_size()

    if visibility.raw_visible and len(smoother.raw_trace) > 1:
        transformed_points = [
            _apply_transform(p, transform, screen_width, screen_height)
            for p in smoother.raw_trace
        ]
        pygame.draw.lines(
            screen,
            RAW_COLOR,
            False,
            transformed_points,
            RAW_LINE_WIDTH,
        )

    if visibility.ma_visible and len(smoother.moving_average_trace) > 1:
        transformed_points = [
            _apply_transform(p, transform, screen_width, screen_height)
            for p in smoother.moving_average_trace
        ]
        pygame.draw.lines(
            screen,
            MOVING_AVERAGE_COLOR,
            False,
            transformed_points,
            SMOOTH_LINE_WIDTH,
        )

    if visibility.exp_visible and len(smoother.exp_trace) > 1:
        transformed_points = [
            _apply_transform(p, transform, screen_width, screen_height)
            for p in smoother.exp_trace
        ]
        pygame.draw.lines(
            screen,
            EXP_COLOR,
            False,
            transformed_points,
            SMOOTH_LINE_WIDTH,
        )


def _draw_markers(
    screen: pygame.Surface,
    raw_point: Point,
    ma_point: Optional[Point],
    exp_point: Point,
    transform: ViewTransform,
    visibility: VisibilityState,
) -> None:
    screen_width, screen_height = screen.get_size()

    if visibility.raw_visible:
        x, y = _apply_transform(raw_point, transform, screen_width, screen_height)
        pygame.draw.circle(screen, CURSOR_RAW_COLOR, (x, y), MARKER_RADIUS)

    if visibility.ma_visible and ma_point is not None:
        x, y = _apply_transform(ma_point, transform, screen_width, screen_height)
        pygame.draw.circle(screen, CURSOR_MA_COLOR, (x, y), MARKER_RADIUS)

    if visibility.exp_visible:
        x, y = _apply_transform(exp_point, transform, screen_width, screen_height)
        pygame.draw.circle(screen, CURSOR_EXP_COLOR, (x, y), MARKER_RADIUS)


def _draw_metrics_graph(
    screen: pygame.Surface,
    font: pygame.font.Font,
    metrics: MetricsTracker,
) -> None:
    if not metrics.fps_history or not metrics.latency_history:
        return

    graph_x = METRICS_GRAPH_X
    graph_y = METRICS_GRAPH_Y
    graph_w = METRICS_GRAPH_WIDTH
    graph_h = METRICS_GRAPH_HEIGHT

    pygame.draw.rect(screen, (30, 30, 30), (graph_x, graph_y, graph_w, graph_h))
    pygame.draw.rect(screen, (100, 100, 100), (graph_x, graph_y, graph_w, graph_h), 1)

    fps_data = list(metrics.fps_history)
    latency_data = list(metrics.latency_history)

    if not fps_data or not latency_data:
        return

    fps_max = max(fps_data) if fps_data else 60
    fps_min = min(fps_data) if fps_data else 0
    fps_range = fps_max - fps_min if fps_max > fps_min else 1

    latency_max = max(latency_data) if latency_data else 20
    latency_min = min(latency_data) if latency_data else 0
    latency_range = latency_max - latency_min if latency_max > latency_min else 1

    if len(fps_data) > 1:
        points = []
        for i, fps in enumerate(fps_data):
            x = graph_x + int((i / (len(fps_data) - 1)) * graph_w)
            y = graph_y + graph_h - int(((fps - fps_min) / fps_range) * graph_h)
            points.append((x, y))
        if len(points) > 1:
            pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

    if len(latency_data) > 1:
        points = []
        for i, latency in enumerate(latency_data):
            x = graph_x + int((i / (len(latency_data) - 1)) * graph_w)
            y = graph_y + graph_h - int(((latency - latency_min) / latency_range) * graph_h)
            points.append((x, y))
        if len(points) > 1:
            pygame.draw.lines(screen, (255, 255, 0), False, points, 2)

    label_text = f"FPS: {metrics.get_avg_fps():.1f} | Lat: {metrics.get_avg_latency():.1f}ms"
    label_surf = font.render(label_text, True, HUD_TEXT_COLOR)
    screen.blit(label_surf, (graph_x, graph_y - HUD_LINE_HEIGHT))


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
) -> None:
    lines = [
        f"N (moving_average): {smoother.window_size}",
        f"IIR alpha (exp.smooth): {smoother.alpha:.2f}",
        f"Histórico (H): {'ON' if history_enabled else 'OFF'}",
        f"Tremor: {'ON' if tremor_sim.enabled else 'OFF'} "
        f"(Int: {tremor_sim.intensity:.1f}, Freq: {tremor_sim.frequency:.1f}Hz)",
        f"Zoom: {transform.zoom:.2f}x",
        f"Visibilidade:",
        f"  Raw (1): {'ON' if visibility.raw_visible else 'OFF'}",
        f"  MA (2): {'ON' if visibility.ma_visible else 'OFF'}",
        f"  Exp (3): {'ON' if visibility.exp_visible else 'OFF'}",
        "",
        "Controles:",
        "  UP / DOWN    -> aumenta/diminui N",
        "  RIGHT / LEFT -> aumenta/diminui IIR alpha",
        "  H            -> liga/desliga histórico",
        "  1, 2, 3      -> toggle visibilidade",
        "  Scroll       -> zoom in/out",
        "  Botão Meio   -> pan (arrastar)",
        "  R            -> reset zoom/pan",
        "  F11          -> tela cheia",
        "  G            -> gerar gráfico 3D",
        "  ESC          -> sair",
    ]

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
    transform: ViewTransform,
    visibility: VisibilityState,
    metrics: MetricsTracker,
    param_indicator: ParamChangeIndicator,
    fullscreen: bool,
    tremor_sim,
) -> None:
    screen.fill(BACKGROUND_COLOR)
    
    if history_enabled:
        _draw_traces(screen, smoother, transform, visibility)
    
    _draw_markers(screen, raw_point, ma_point, exp_point, transform, visibility)
    _draw_hud(screen, font, smoother, history_enabled, visibility, transform, fullscreen, tremor_sim)
    _draw_metrics_graph(screen, font, metrics)
    _draw_param_change_indicator(screen, font, param_indicator)
    
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
