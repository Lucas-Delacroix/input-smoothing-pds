from dataclasses import dataclass
from typing import Optional, Tuple
import time

import pygame

from tremor_simulator import TremorSimulator


@dataclass(frozen=True)
class FieldConfig:
    label: str
    attr: str
    field_type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: float = 0.5


class TremorModal:
    MODAL_WIDTH = 850
    MODAL_HEIGHT = 600
    MODAL_ANIM_DISTANCE = 50
    OVERLAY_ALPHA = 180
    SHADOW_OFFSET = 8
    FIELD_MARGIN_X = 50
    FIELD_HEIGHT = 95
    FIELD_TOP = 110
    FIELD_SPACING = 110
    LABEL_OFFSET_X = 15
    LABEL_OFFSET_Y = 18
    SLIDER_HEIGHT = 14
    SLIDER_DETECTION_HEIGHT = 60
    SLIDER_OFFSET_Y = 55
    SLIDER_PADDING_X = 15
    VALUE_MARGIN_RIGHT = 20
    TOGGLE_SIZE = 70
    TOGGLE_HEIGHT = 35
    TOGGLE_MARGIN_RIGHT = 20

    FIELDS: Tuple[FieldConfig, ...] = (
        FieldConfig("Ativar Tremor", "temp_enabled", "bool"),
        FieldConfig("Intensidade", "temp_intensity", "float", 0.0, 50.0, 0.5),
        FieldConfig("Frequência (Hz)", "temp_frequency", "float", 0.1, 50.0, 0.5),
    )

    def __init__(self, tremor_sim: TremorSimulator, font: pygame.font.Font):
        self.tremor_sim = tremor_sim
        self.font = font
        self.active = False
        self.selected_field = 0
        self.temp_enabled = False
        self.temp_intensity = 5.0
        self.temp_frequency = 10.0
        self.input_text = ""
        self.editing_field = False
        self.slider_dragging = False
        self.slider_drag_field: Optional[int] = None
        self.open_time = 0.0

    def open(self) -> None:
        self.active = True
        self._sync_from_simulator()
        self.selected_field = 0
        self.editing_field = False
        self.input_text = ""
        self.slider_dragging = False
        self.slider_drag_field = None
        self.open_time = time.time()

    def close(self) -> None:
        self._apply_changes()
        self.active = False
        self.editing_field = False
        self.input_text = ""
        self.slider_dragging = False
        self.slider_drag_field = None

    def handle_key(self, key: int, mod: int) -> bool:
        if not self.active:
            return False

        if key == pygame.K_ESCAPE:
            self.close()
            return True

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.editing_field:
                self._apply_input()
            else:
                self.close()
            return True

        if self.editing_field:
            return self._handle_editing_input(key)

        if key == pygame.K_UP:
            self._move_selection(-1)
            return True

        if key == pygame.K_DOWN:
            self._move_selection(1)
            return True

        if key == pygame.K_LEFT:
            self._adjust_selected_field(-1)
            return True

        if key == pygame.K_RIGHT:
            self._adjust_selected_field(1)
            return True

        if key == pygame.K_TAB:
            self._move_selection(1)
            return True

        if key == pygame.K_SPACE:
            self._toggle_or_edit_current()
            return True

        return False

    def handle_mouse(self, pos: Tuple[int, int], button: int, pressed: bool) -> bool:
        if not self.active:
            return False

        layout = self._layout()

        if button == 1 and pressed:
            slider_hit = self._slider_at_position(pos, layout)
            if slider_hit is not None:
                self.slider_dragging = True
                self.slider_drag_field = slider_hit
                self._update_slider_from_mouse(pos[0], layout, slider_hit)
                return True

        if button == 1 and not pressed:
            if self.slider_dragging:
                self.slider_dragging = False
                self.slider_drag_field = None
                return True

        if button == 0 and self.slider_dragging and self.slider_drag_field is not None:
            self._update_slider_from_mouse(pos[0], layout, self.slider_drag_field)
            return True

        return False

    def render(self, screen: pygame.Surface) -> None:
        if not self.active:
            return

        layout = self._layout(screen.get_size())
        self._draw_overlay(screen, layout.anim_progress)
        self._draw_modal_base(screen, layout)
        self._draw_title_and_header(screen, layout)
        self._draw_fields(screen, layout)
        self._draw_footer(screen, layout)

    def _handle_editing_input(self, key: int) -> bool:
        if key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return True

        if key in (pygame.K_PERIOD, pygame.K_KP_PERIOD):
            if "." not in self.input_text:
                self.input_text += "."
            return True

        if pygame.K_0 <= key <= pygame.K_9 or pygame.K_KP0 <= key <= pygame.K_KP9:
            digit = str(key - pygame.K_0) if key <= pygame.K_9 else str(key - pygame.K_KP0)
            self.input_text += digit
            return True

        return False

    def _move_selection(self, delta: int) -> None:
        total_fields = len(self.FIELDS)
        self.selected_field = (self.selected_field + delta) % total_fields

    def _toggle_or_edit_current(self) -> None:
        field = self.FIELDS[self.selected_field]
        if field.field_type == "bool":
            self.temp_enabled = not self.temp_enabled
            self._apply_changes()
            return

        self.editing_field = True
        self.input_text = f"{self._get_field_value(field):.2f}"

    def _adjust_selected_field(self, direction: int) -> None:
        field = self.FIELDS[self.selected_field]
        if field.field_type == "bool":
            self.temp_enabled = not self.temp_enabled
            self._apply_changes()
            return

        new_value = self._get_field_value(field) + direction * field.step
        clamped = self._clamp(new_value, field.min_value, field.max_value)
        self._set_field_value(field, clamped)
        self._apply_changes()

    def _apply_input(self) -> None:
        field = self.FIELDS[self.selected_field]
        try:
            value = float(self.input_text)
        except ValueError:
            self._reset_edit_state()
            return

        clamped = self._clamp(value, field.min_value, field.max_value)
        self._set_field_value(field, clamped)
        self._apply_changes()
        self._reset_edit_state()

    def _reset_edit_state(self) -> None:
        self.editing_field = False
        self.input_text = ""

    def _update_slider_from_mouse(self, mouse_x: int, layout: "ModalLayout", field_index: int) -> None:
        field_rect = self._field_rect(layout, field_index)
        slider_x, _, slider_width = self._slider_geometry(field_rect)
        ratio = (mouse_x - slider_x) / slider_width
        ratio = self._clamp(ratio, 0.0, 1.0)

        field = self.FIELDS[field_index]
        min_value = field.min_value or 0.0
        max_value = field.max_value or min_value
        value = min_value + ratio * (max_value - min_value)
        self._set_field_value(field, value)
        self._apply_changes()

    def _slider_at_position(self, pos: Tuple[int, int], layout: "ModalLayout") -> Optional[int]:
        for index, field in enumerate(self.FIELDS):
            if field.field_type != "float":
                continue
            field_rect = self._field_rect(layout, index)
            slider_x, slider_y, slider_width = self._slider_geometry(field_rect)
            if (
                slider_x <= pos[0] <= slider_x + slider_width
                and slider_y <= pos[1] <= slider_y + self.SLIDER_DETECTION_HEIGHT
            ):
                return index
        return None

    def _field_rect(self, layout: "ModalLayout", index: int) -> pygame.Rect:
        return pygame.Rect(
            layout.x + self.FIELD_MARGIN_X,
            layout.y + self.FIELD_TOP + index * self.FIELD_SPACING,
            layout.width - 2 * self.FIELD_MARGIN_X,
            self.FIELD_HEIGHT,
        )

    def _layout(self, screen_size: Optional[Tuple[int, int]] = None) -> "ModalLayout":
        if screen_size is None:
            screen_size = pygame.display.get_surface().get_size()

        screen_width, screen_height = screen_size
        modal_x = (screen_width - self.MODAL_WIDTH) // 2
        modal_y = (screen_height - self.MODAL_HEIGHT) // 2

        anim_progress = self._animation_progress()
        modal_offset_y = (1.0 - anim_progress) * self.MODAL_ANIM_DISTANCE
        actual_modal_y = int(modal_y + modal_offset_y)

        return ModalLayout(
            x=modal_x,
            y=actual_modal_y,
            width=self.MODAL_WIDTH,
            height=self.MODAL_HEIGHT,
            anim_progress=anim_progress,
        )

    def _draw_overlay(self, screen: pygame.Surface, anim_progress: float) -> None:
        overlay_alpha = int(self.OVERLAY_ALPHA * anim_progress)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        screen.blit(overlay, (0, 0))

    def _draw_modal_base(self, screen: pygame.Surface, layout: "ModalLayout") -> None:
        shadow_surf = pygame.Surface(
            (layout.width + self.SHADOW_OFFSET * 2, layout.height + self.SHADOW_OFFSET * 2),
            pygame.SRCALPHA,
        )
        shadow_surf.fill((0, 0, 0, 120))
        screen.blit(shadow_surf, (layout.x - self.SHADOW_OFFSET, layout.y - self.SHADOW_OFFSET))

        pygame.draw.rect(
            screen,
            (25, 28, 32),
            (layout.x, layout.y, layout.width, layout.height),
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            (70, 120, 200),
            (layout.x, layout.y, layout.width, layout.height),
            3,
            border_radius=10,
        )

    def _draw_title_and_header(self, screen: pygame.Surface, layout: "ModalLayout") -> None:
        title_text = "Configuração de Tremor"
        title = self.font.render(title_text, True, (255, 255, 255))
        title_rect = title.get_rect(center=(layout.x + layout.width // 2, layout.y + 50))
        screen.blit(title, title_rect)

        separator_y = layout.y + 85
        pygame.draw.line(
            screen,
            (70, 120, 200),
            (layout.x + 50, separator_y),
            (layout.x + layout.width - 50, separator_y),
            2,
        )

    def _draw_fields(self, screen: pygame.Surface, layout: "ModalLayout") -> None:
        for index, field in enumerate(self.FIELDS):
            value = self._get_field_value(field)
            is_selected = index == self.selected_field
            is_editing = is_selected and self.editing_field
            field_rect = self._field_rect(layout, index)

            self._draw_field_box(screen, field_rect, is_selected)
            self._draw_field_label(screen, field.label, field_rect)

            if field.field_type == "bool":
                self._draw_toggle(screen, field_rect, bool(value))
            else:
                self._draw_value(screen, field_rect, value, is_editing)
                self._draw_slider(screen, field_rect, index, value)

    def _draw_field_box(
        self,
        screen: pygame.Surface,
        field_rect: pygame.Rect,
        is_selected: bool,
    ) -> None:
        bg_color = (45, 55, 65) if is_selected else (35, 40, 45)
        pygame.draw.rect(screen, bg_color, field_rect, border_radius=8)

        if is_selected:
            border_color = (100, 150, 255)
            pygame.draw.rect(screen, border_color, field_rect, 2, border_radius=8)

    def _draw_field_label(self, screen: pygame.Surface, label: str, field_rect: pygame.Rect) -> None:
        label_text = self.font.render(f"{label}:", True, (220, 220, 220))
        screen.blit(label_text, (field_rect.x + self.LABEL_OFFSET_X, field_rect.y + self.LABEL_OFFSET_Y))

    def _draw_toggle(self, screen: pygame.Surface, field_rect: pygame.Rect, enabled: bool) -> None:
        toggle_x = field_rect.right - self.TOGGLE_MARGIN_RIGHT - self.TOGGLE_SIZE
        toggle_y = field_rect.centery - self.TOGGLE_HEIGHT // 2

        toggle_bg = (80, 80, 80) if not enabled else (50, 200, 50)
        pygame.draw.rect(
            screen,
            toggle_bg,
            (toggle_x, toggle_y, self.TOGGLE_SIZE, self.TOGGLE_HEIGHT),
            border_radius=17,
        )

        toggle_pos = toggle_x + (self.TOGGLE_SIZE - 28) if enabled else toggle_x + 4
        toggle_color = (240, 240, 240)
        pygame.draw.circle(screen, toggle_color, (int(toggle_pos + 14), toggle_y + 17), 14)

        status_text = "ON" if enabled else "OFF"
        status_color = (0, 255, 100) if enabled else (180, 180, 180)
        status_surf = self.font.render(status_text, True, status_color)
        status_x = toggle_x - 85
        screen.blit(status_surf, (status_x, field_rect.centery - 10))

    def _draw_value(
        self,
        screen: pygame.Surface,
        field_rect: pygame.Rect,
        value: float,
        is_editing: bool,
    ) -> None:
        value_text = self.input_text if is_editing and self.input_text else f"{value:.2f}"
        value_surf = self.font.render(value_text, True, (255, 255, 255))
        value_x = field_rect.right - self.VALUE_MARGIN_RIGHT - value_surf.get_width()
        screen.blit(value_surf, (value_x, field_rect.y + self.LABEL_OFFSET_Y))

    def _draw_slider(
        self,
        screen: pygame.Surface,
        field_rect: pygame.Rect,
        field_index: int,
        value: float,
    ) -> None:
        slider_x, slider_y, slider_width = self._slider_geometry(field_rect)

        field = self.FIELDS[field_index]
        min_value = field.min_value or 0.0
        max_value = field.max_value or min_value
        ratio = (value - min_value) / (max_value - min_value) if max_value > min_value else 0.0
        slider_pos = slider_x + ratio * slider_width

        pygame.draw.rect(screen, (40, 40, 40), (slider_x, slider_y, slider_width, self.SLIDER_HEIGHT), border_radius=5)
        filled_width = ratio * slider_width
        if field_index == 1:
            gradient_color = (255, int(120 + ratio * 135), int(120 + ratio * 135))
        else:
            gradient_color = (int(120 + ratio * 135), int(120 + ratio * 135), 255)
        pygame.draw.rect(screen, gradient_color, (slider_x, slider_y, filled_width, self.SLIDER_HEIGHT), border_radius=5)

        handle_size = 18
        dragging_current = self.slider_dragging and self.slider_drag_field == field_index
        handle_color = (255, 255, 100) if dragging_current else (220, 220, 220)
        handle_y = slider_y + self.SLIDER_HEIGHT // 2
        pygame.draw.circle(screen, handle_color, (int(slider_pos), handle_y), handle_size // 2)
        pygame.draw.circle(screen, (60, 60, 60), (int(slider_pos), handle_y), handle_size // 2, 2)

    def _draw_footer(self, screen: pygame.Surface, layout: "ModalLayout") -> None:
        preview_y = layout.y + layout.height - 110
        preview_text = f"Preview: {'Ativo' if self.temp_enabled else 'Inativo'}"
        preview_surf = self.font.render(preview_text, True, (150, 200, 255))
        screen.blit(preview_surf, (layout.x + 65, preview_y))

        help_lines = [
            "←/→: Ajustar  |  ↑/↓: Navegar  |  Enter: Aplicar  |  ESC: Fechar",
            "Clique e arraste nos sliders para ajustar valores",
        ]

        help_start_y = layout.y + layout.height - 70
        for index, text in enumerate(help_lines):
            help_surf = self.font.render(text, True, (140, 140, 140))
            help_x = layout.x + (layout.width - help_surf.get_width()) // 2
            help_y = help_start_y + index * 28
            if help_y + 28 <= layout.y + layout.height - 15:
                screen.blit(help_surf, (help_x, help_y))

    def _slider_geometry(self, field_rect: pygame.Rect) -> Tuple[int, int, int]:
        slider_x = field_rect.x + self.SLIDER_PADDING_X
        slider_width = field_rect.width - 2 * self.SLIDER_PADDING_X
        slider_y = field_rect.y + self.SLIDER_OFFSET_Y
        return slider_x, slider_y, slider_width

    def _get_field_value(self, field: FieldConfig) -> float:
        return getattr(self, field.attr)

    def _set_field_value(self, field: FieldConfig, value: float) -> None:
        setattr(self, field.attr, value)

    def _apply_changes(self) -> None:
        self.tremor_sim.set_enabled(self.temp_enabled)
        self.tremor_sim.set_intensity(self.temp_intensity)
        self.tremor_sim.set_frequency(self.temp_frequency)

    def _sync_from_simulator(self) -> None:
        self.temp_enabled = self.tremor_sim.enabled
        self.temp_intensity = self.tremor_sim.intensity
        self.temp_frequency = self.tremor_sim.frequency

    def _animation_progress(self) -> float:
        if self.open_time == 0.0:
            self.open_time = time.time()
        return min(1.0, (time.time() - self.open_time) * 3.0)

    @staticmethod
    def _clamp(value: float, min_value: Optional[float], max_value: Optional[float]) -> float:
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return value


@dataclass(frozen=True)
class ModalLayout:
    x: int
    y: int
    width: int
    height: int
    anim_progress: float
