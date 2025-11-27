import sys
from typing import Optional

import pygame

from config import (
    ALPHA_MAX,
    ALPHA_MIN,
    ALPHA_STEP,
    BACKGROUND_COLOR,
    CURSOR_EXP_COLOR,
    CURSOR_MA_COLOR,
    CURSOR_RAW_COLOR,
    DEFAULT_IIR_ALPHA,
    DEFAULT_MOVING_AVERAGE_WINDOW,
    EXP_COLOR,
    FPS,
    HUD_FONT,
    HUD_FONT_SIZE,
    HUD_LINE_HEIGHT,
    HUD_MARGIN_X,
    HUD_MARGIN_Y,
    HUD_TEXT_COLOR,
    MARKER_RADIUS,
    MAX_BUFFER,
    MOVING_AVERAGE_COLOR,
    MOVING_AVERAGE_MIN,
    RAW_COLOR,
    RAW_LINE_WIDTH,
    SMOOTH_LINE_WIDTH,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from input_device import InputSmoother, Point


def create_window() -> pygame.Surface:
    pygame.display.set_caption(TITLE)
    return pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))


def build_font() -> pygame.font.Font:
    return pygame.font.SysFont(HUD_FONT, HUD_FONT_SIZE)


def handle_events(smoother: InputSmoother) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            handle_key(event.key, smoother)

    return True


def handle_key(key: int, smoother: InputSmoother) -> None:
    if key == pygame.K_UP:
        smoother.change_window(1)
    elif key == pygame.K_DOWN:
        smoother.change_window(-1)
    elif key == pygame.K_RIGHT:
        smoother.change_alpha(ALPHA_STEP)
    elif key == pygame.K_LEFT:
        smoother.change_alpha(-ALPHA_STEP)


def draw_traces(screen: pygame.Surface, smoother: InputSmoother) -> None:
    if len(smoother.raw_trace) > 1:
        pygame.draw.lines(
            screen,
            RAW_COLOR,
            False,
            smoother.raw_trace.as_int_tuples(),
            RAW_LINE_WIDTH,
        )

    if len(smoother.moving_average_trace) > 1:
        pygame.draw.lines(
            screen,
            MOVING_AVERAGE_COLOR,
            False,
            smoother.moving_average_trace.as_int_tuples(),
            SMOOTH_LINE_WIDTH,
        )

    if len(smoother.exp_trace) > 1:
        pygame.draw.lines(
            screen,
            EXP_COLOR,
            False,
            smoother.exp_trace.as_int_tuples(),
            SMOOTH_LINE_WIDTH,
        )


def draw_markers(
    screen: pygame.Surface,
    raw_point: Point,
    ma_point: Optional[Point],
    exp_point: Point,
) -> None:
    pygame.draw.circle(screen, CURSOR_RAW_COLOR, raw_point.as_int_tuple(), MARKER_RADIUS)

    if ma_point is not None:
        pygame.draw.circle(
            screen,
            CURSOR_MA_COLOR,
            ma_point.as_int_tuple(),
            MARKER_RADIUS,
        )

    pygame.draw.circle(screen, CURSOR_EXP_COLOR, exp_point.as_int_tuple(), MARKER_RADIUS)


def draw_hud(screen: pygame.Surface, font: pygame.font.Font, smoother: InputSmoother) -> None:
    lines = [
        f"N (moving_average): {smoother.window_size}",
        f"IIR alpha (exp.smooth): {smoother.alpha:.2f}",
        "Controles:",
        "  UP / DOWN    -> aumenta/diminui N",
        "  RIGHT / LEFT -> aumenta/diminui IIR alpha",
        "  ESC          -> sair",
    ]

    x, y = HUD_MARGIN_X, HUD_MARGIN_Y
    for line in lines:
        surf = font.render(line, True, HUD_TEXT_COLOR)
        screen.blit(surf, (x, y))
        y += HUD_LINE_HEIGHT


def render_frame(
    screen: pygame.Surface,
    font: pygame.font.Font,
    smoother: InputSmoother,
    raw_point: Point,
    ma_point: Optional[Point],
    exp_point: Point,
) -> None:
    screen.fill(BACKGROUND_COLOR)
    draw_traces(screen, smoother)
    draw_markers(screen, raw_point, ma_point, exp_point)
    draw_hud(screen, font, smoother)
    pygame.display.flip()


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

    running = True
    while running:
        running = handle_events(smoother)
        if not running:
            break

        mouse_x, mouse_y = pygame.mouse.get_pos()
        raw_point, ma_point, exp_point = smoother.add_sample(mouse_x, mouse_y)

        render_frame(screen, font, smoother, raw_point, ma_point, exp_point)
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
