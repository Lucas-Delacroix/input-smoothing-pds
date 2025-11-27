import sys
import pygame
from filters import moving_average, exp_smoothing

def config_window():
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Realtime Input Smoothing - PDS")
    return screen

def draw_hud(screen: pygame.Surface, n_moving_average: int, IIR_factor: float) -> None:
    font = pygame.font.SysFont("consolas", 20)

    lines = [
        f"N (moving_average): {n_moving_average}",
        f"IIR_factor (exp.smooth): {IIR_factor:.2f}",
        "Controles:",
        "  ↑ / ↓  -> aumenta/diminui N",
        "  → / ←  -> aumenta/diminui IIR_factor",
        "  ESC    -> sair",
    ]

    x, y = 10, 10
    for line in lines:
        surf = font.render(line, True, (230, 230, 230))
        screen.blit(surf, (x, y))
        y += 22

def main():
    pygame.init()
    screen = config_window()
    clock = pygame.time.Clock()

    n_moving_average = 5
    IIR_factor = 0.4
    raw_x = []
    raw_y = []
    exp_x = None
    exp_y = None



    running = True
    while running:
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    n_moving_average += 1
                elif event.key == pygame.K_DOWN:
                    n_moving_average = max(1, n_moving_average - 1)
                elif event.key == pygame.K_RIGHT:
                    IIR_factor = min(1.0, IIR_factor + 0.05)
                elif event.key == pygame.K_LEFT:
                    IIR_factor = max(0.05, IIR_factor - 0.05)


        mouse_x, mouse_y = pygame.mouse.get_pos()
        raw_x.append(mouse_x)
        raw_y.append(mouse_y)


        ma_x = moving_average(raw_x, n_moving_average)
        ma_y = moving_average(raw_y, n_moving_average)

        exp_x = exp_smoothing(mouse_x, exp_x, IIR_factor)
        exp_y = exp_smoothing(mouse_y, exp_y, IIR_factor)

        screen.fill((10, 10, 10))

        pygame.draw.circle(screen, (200, 50, 50), (mouse_x, mouse_y), 6)

        if ma_x is not None and ma_y is not None:
            pygame.draw.circle(screen, (50, 200, 50), (int(ma_x), int(ma_y)), 6)

        pygame.draw.circle(screen, (50, 100, 220), (int(exp_x), int(exp_y)), 6)

        draw_hud(screen, n_moving_average, IIR_factor)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()





if __name__ == "__main__":
    main()
