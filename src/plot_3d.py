from typing import Optional
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from input_device import InputSmoother


def generate_3d_plot(smoother: InputSmoother, output_path: Optional[str] = None) -> None:
    raw_points = list(smoother.raw_trace)
    ma_points = list(smoother.moving_average_trace)
    exp_points = list(smoother.exp_trace)

    if not raw_points:
        print("Nenhum dado disponível para plotar.")
        return

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    time_steps = np.arange(len(raw_points))

    raw_x = [p.x for p in raw_points]
    raw_y = [p.y for p in raw_points]

    ma_x = [p.x for p in ma_points] if ma_points else []
    ma_y = [p.y for p in ma_points] if ma_points else []

    exp_x = [p.x for p in exp_points]
    exp_y = [p.y for p in exp_points]

    if raw_x and raw_y:
        ax.plot(raw_x, raw_y, time_steps, 
                color='red', linewidth=1, alpha=0.6, label='Raw Input')

    if ma_x and ma_y and len(ma_x) == len(time_steps[:len(ma_x)]):
        ma_time = time_steps[:len(ma_x)]
        ax.plot(ma_x, ma_y, ma_time,
                color='green', linewidth=2, alpha=0.8, label='Moving Average')

    if exp_x and exp_y:
        ax.plot(exp_x, exp_y, time_steps,
                color='blue', linewidth=2, alpha=0.8, label='Exponential Smoothing')

    ax.set_xlabel('X Position', fontsize=10)
    ax.set_ylabel('Y Position', fontsize=10)
    ax.set_zlabel('Time (samples)', fontsize=10)
    ax.set_title('3D Visualization of Input Smoothing\n'
                 f'Window Size: {smoother.window_size}, Alpha: {smoother.alpha:.2f}',
                 fontsize=12, fontweight='bold')
    ax.legend(loc='upper left')

    ax.view_init(elev=20, azim=45)

    ax.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Gráfico 3D salvo em: {output_path}")
    else:
        plt.show()

    plt.close()


def generate_3d_surface_map(smoother: InputSmoother, output_path: Optional[str] = None) -> None:
    raw_points = list(smoother.raw_trace)
    
    if not raw_points or len(raw_points) < 10:
        print("Dados insuficientes para gerar mapa de superfície.")
        return

    fig = plt.figure(figsize=(14, 10))
    
    ax1 = fig.add_subplot(221, projection='3d')
    _plot_density_map(ax1, raw_points, 'Raw Input Density Map', 'Reds')
    
    if smoother.moving_average_trace:
        ma_points = list(smoother.moving_average_trace)
        ax2 = fig.add_subplot(222, projection='3d')
        _plot_density_map(ax2, ma_points, 'Moving Average Density Map', 'Greens')
    
    exp_points = list(smoother.exp_trace)
    ax3 = fig.add_subplot(223, projection='3d')
    _plot_density_map(ax3, exp_points, 'Exponential Smoothing Density Map', 'Blues')
    
    ax4 = fig.add_subplot(224, projection='3d')
    time_steps = np.arange(len(raw_points))
    raw_x = [p.x for p in raw_points]
    raw_y = [p.y for p in raw_points]
    exp_x = [p.x for p in exp_points]
    exp_y = [p.y for p in exp_points]
    
    ax4.plot(raw_x, raw_y, time_steps, 'r-', alpha=0.3, linewidth=1, label='Raw')
    ax4.plot(exp_x, exp_y, time_steps, 'b-', alpha=0.7, linewidth=2, label='Smoothed')
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    ax4.set_zlabel('Time')
    ax4.set_title('Raw vs Smoothed Comparison')
    ax4.legend()
    ax4.view_init(elev=20, azim=45)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Mapa 3D salvo em: {output_path}")
    else:
        plt.show()

    plt.close()


def _plot_density_map(ax, points, title, colormap):
    if not points:
        return
    
    x_coords = [p.x for p in points]
    y_coords = [p.y for p in points]
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_min -= x_range * 0.1
    x_max += x_range * 0.1
    y_min -= y_range * 0.1
    y_max += y_range * 0.1
    
    grid_size = 30
    x_grid = np.linspace(x_min, x_max, grid_size)
    y_grid = np.linspace(y_min, y_max, grid_size)
    X, Y = np.meshgrid(x_grid, y_grid)
    
    Z = np.zeros_like(X)
    for px, py in zip(x_coords, y_coords):
        dist_sq = (X - px)**2 + (Y - py)**2
        sigma = min(x_range, y_range) / 10
        Z += np.exp(-dist_sq / (2 * sigma**2))
    
    if Z.max() > 0:
        Z = Z / Z.max()
    
    surf = ax.plot_surface(X, Y, Z, cmap=colormap, alpha=0.7, linewidth=0, antialiased=True)
    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_zlabel('Density')
    ax.set_title(title)
    ax.view_init(elev=30, azim=45)
    ax.figure.colorbar(surf, ax=ax, shrink=0.5)

