from typing import Optional
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from input_device import InputSmoother


def generate_3d_plot(smoother: InputSmoother, output_path: Optional[str] = None) -> None:
    raw_points = list(smoother.raw_trace)
    ma_points = list(smoother.moving_average_trace)
    exp_points = list(smoother.exp_trace)
    drift_points = list(getattr(smoother, "drift_corrected_trace", []))

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

    drift_x = [p.x for p in drift_points] if drift_points else []
    drift_y = [p.y for p in drift_points] if drift_points else []

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

    if drift_x and drift_y:
        drift_time = time_steps[:len(drift_x)]
        ax.plot(drift_x, drift_y, drift_time,
                color='gold', linewidth=2, alpha=0.9, label='Drift Corrected')

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
    ma_points = list(smoother.moving_average_trace)
    exp_points = list(smoother.exp_trace)
    drift_points = list(getattr(smoother, "drift_corrected_trace", []))
    
    if not raw_points or len(raw_points) < 10:
        print("Dados insuficientes para gerar mapa de superfície.")
        return

    fig = plt.figure(figsize=(16, 12))
    
    # Raw
    ax1 = fig.add_subplot(221, projection='3d')
    _plot_density_map(ax1, raw_points, 'Raw Input Density Map', 'Reds')
    
    # Moving Average
    ax2 = fig.add_subplot(222, projection='3d')
    _plot_density_map(ax2, ma_points, 'Moving Average Density Map', 'Greens')
    
    # Exponential Smoothing
    ax3 = fig.add_subplot(223, projection='3d')
    _plot_density_map(ax3, exp_points, 'Exponential Smoothing Density Map', 'Blues')
    
    # Drift Corrected
    ax4 = fig.add_subplot(224, projection='3d')
    _plot_density_map(ax4, drift_points, 'Drift Corrected Density Map', 'YlOrBr')

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
