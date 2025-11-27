from typing import Optional, Tuple
import pygame
import time

from tremor_simulator import TremorSimulator


class TremorModal:
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
        self.animation_time = 0.0
        self.slider_dragging = False
        self.slider_drag_field = None
        
    def open(self) -> None:
        self.active = True
        self.temp_enabled = self.tremor_sim.enabled
        self.temp_intensity = self.tremor_sim.intensity
        self.temp_frequency = self.tremor_sim.frequency
        self.selected_field = 0
        self.editing_field = False
        self.input_text = ""
        self.animation_time = time.time()
        self.open_time = time.time()
        self.slider_dragging = False
        
    def close(self) -> None:
        self.active = False
        self.editing_field = False
        self.input_text = ""
        self.slider_dragging = False
        self._apply_changes()
        
    def handle_key(self, key: int, mod: int) -> bool:
        if not self.active:
            return False
            
        if key == pygame.K_ESCAPE:
            self.close()
            return True
            
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self.editing_field:
                self._apply_input()
            else:
                self._apply_changes()
                self.close()
            return True
            
        if key == pygame.K_UP:
            if not self.editing_field:
                self.selected_field = (self.selected_field - 1) % 3
            return True
            
        if key == pygame.K_DOWN:
            if not self.editing_field:
                self.selected_field = (self.selected_field + 1) % 3
            return True
            
        if key == pygame.K_LEFT:
            if not self.editing_field:
                if self.selected_field == 0:
                    self.temp_enabled = not self.temp_enabled
                    self._apply_changes()
                elif self.selected_field == 1:
                    self.temp_intensity = max(0.0, self.temp_intensity - 0.5)
                    self._apply_changes()
                elif self.selected_field == 2:
                    self.temp_frequency = max(0.1, self.temp_frequency - 0.5)
                    self._apply_changes()
            return True
            
        if key == pygame.K_RIGHT:
            if not self.editing_field:
                if self.selected_field == 0:
                    self.temp_enabled = not self.temp_enabled
                    self._apply_changes()
                elif self.selected_field == 1:
                    self.temp_intensity = min(50.0, self.temp_intensity + 0.5)
                    self._apply_changes()
                elif self.selected_field == 2:
                    self.temp_frequency = min(50.0, self.temp_frequency + 0.5)
                    self._apply_changes()
            return True
            
        if key == pygame.K_TAB:
            if not self.editing_field:
                self.selected_field = (self.selected_field + 1) % 3
            return True
            
        if key == pygame.K_BACKSPACE:
            if self.editing_field:
                self.input_text = self.input_text[:-1]
            return True
            
        if self.editing_field:
            if key == pygame.K_PERIOD or key == pygame.K_KP_PERIOD:
                if '.' not in self.input_text:
                    self.input_text += '.'
                return True
            if pygame.K_0 <= key <= pygame.K_9 or pygame.K_KP0 <= key <= pygame.K_KP9:
                digit = str(key - pygame.K_0) if key <= pygame.K_9 else str(key - pygame.K_KP0)
                self.input_text += digit
                return True
        else:
            if key == pygame.K_RETURN or key == pygame.K_KP_ENTER or key == pygame.K_SPACE:
                if self.selected_field == 0:
                    self.temp_enabled = not self.temp_enabled
                    self._apply_changes()
                else:
                    self.editing_field = True
                    if self.selected_field == 1:
                        self.input_text = str(self.temp_intensity)
                    elif self.selected_field == 2:
                        self.input_text = str(self.temp_frequency)
                return True
                
        return False
        
    def handle_mouse(self, pos: Tuple[int, int], button: int, pressed: bool) -> bool:
        if not self.active:
            return False
            
        screen_width, screen_height = pygame.display.get_surface().get_size()
        modal_width = 850
        modal_height = 600
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        slider_y_start = modal_y + 160
        slider_height = 110
        
        if button == 1:
            if pressed:
                for i in [1, 2]:
                    slider_x = modal_x + 65
                    slider_y = slider_y_start + i * slider_height
                    slider_width = modal_width - 130
                    
                    if slider_x <= pos[0] <= slider_x + slider_width and slider_y <= pos[1] <= slider_y + 60:
                        self.slider_dragging = True
                        self.slider_drag_field = i
                        self._update_slider_from_mouse(pos[0], slider_x, slider_width, i)
                        return True
            else:
                if self.slider_dragging:
                    self.slider_dragging = False
                    self.slider_drag_field = None
                    return True
                    
        if self.slider_dragging and button == 0:
            if self.slider_drag_field:
                slider_x = modal_x + 65
                slider_width = modal_width - 130
                self._update_slider_from_mouse(pos[0], slider_x, slider_width, self.slider_drag_field)
                return True
                
        return False
        
    def _update_slider_from_mouse(self, mouse_x: int, slider_x: int, slider_width: int, field: int) -> None:
        ratio = max(0.0, min(1.0, (mouse_x - slider_x) / slider_width))
        if field == 1:
            self.temp_intensity = ratio * 50.0
            self._apply_changes()
        elif field == 2:
            self.temp_frequency = 0.1 + ratio * 49.9
            self._apply_changes()
        
    def _apply_input(self) -> None:
        try:
            value = float(self.input_text)
            if self.selected_field == 1:
                self.temp_intensity = max(0.0, min(50.0, value))
            elif self.selected_field == 2:
                self.temp_frequency = max(0.1, min(50.0, value))
            self._apply_changes()
        except ValueError:
            pass
        self.editing_field = False
        self.input_text = ""
        
    def _apply_changes(self) -> None:
        self.tremor_sim.set_enabled(self.temp_enabled)
        self.tremor_sim.set_intensity(self.temp_intensity)
        self.tremor_sim.set_frequency(self.temp_frequency)
        
    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surf = self.font.render(word, True, (255, 255, 255))
            word_width = word_surf.get_width()
            
            if current_width + word_width + (len(current_line) * 5) > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width + 5
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
        
    def render(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        current_time = time.time()
        if not hasattr(self, 'open_time') or self.open_time == 0:
            self.open_time = current_time
        anim_progress = min(1.0, (current_time - self.open_time) * 3.0)
        
        screen_width, screen_height = screen.get_size()
        modal_width = 850
        modal_height = 600
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        overlay_alpha = int(180 * anim_progress)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        screen.blit(overlay, (0, 0))
        
        modal_offset_y = (1.0 - anim_progress) * 50
        actual_modal_y = int(modal_y + modal_offset_y)
        
        shadow_offset = 8
        shadow_surf = pygame.Surface((modal_width + shadow_offset * 2, modal_height + shadow_offset * 2), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 120))
        screen.blit(shadow_surf, (modal_x - shadow_offset, actual_modal_y - shadow_offset))
        
        pygame.draw.rect(screen, (25, 28, 32), (modal_x, actual_modal_y, modal_width, modal_height), border_radius=10)
        pygame.draw.rect(screen, (70, 120, 200), (modal_x, actual_modal_y, modal_width, modal_height), 3, border_radius=10)
        
        title_text = "Configuração de Tremor"
        title = self.font.render(title_text, True, (255, 255, 255))
        title_rect = title.get_rect(center=(modal_x + modal_width // 2, actual_modal_y + 50))
        screen.blit(title, title_rect)
        
        separator_y = actual_modal_y + 85
        pygame.draw.line(screen, (70, 120, 200), (modal_x + 50, separator_y), (modal_x + modal_width - 50, separator_y), 2)
        
        y_offset = actual_modal_y + 110
        line_height = 110
        
        fields = [
            ("Ativar Tremor", self.temp_enabled, "bool", None),
            ("Intensidade", self.temp_intensity, "float", (0.0, 50.0)),
            ("Frequência (Hz)", self.temp_frequency, "float", (0.1, 50.0)),
        ]
        
        for i, (label, value, field_type, value_range) in enumerate(fields):
            is_selected = i == self.selected_field
            is_editing = is_selected and self.editing_field
            
            bg_color = (45, 55, 65) if is_selected else (35, 40, 45)
            
            field_rect = pygame.Rect(modal_x + 50, y_offset, modal_width - 100, 95)
            pygame.draw.rect(screen, bg_color, field_rect, border_radius=8)
            
            if is_selected:
                border_color = (100, 150, 255)
                pygame.draw.rect(screen, border_color, field_rect, 2, border_radius=8)
            
            label_text = self.font.render(label + ":", True, (220, 220, 220))
            screen.blit(label_text, (modal_x + 65, y_offset + 18))
            
            if field_type == "bool":
                toggle_size = 70
                toggle_x = modal_x + modal_width - 100
                toggle_y = y_offset + 28
                
                toggle_bg = (80, 80, 80) if not value else (50, 200, 50)
                pygame.draw.rect(screen, toggle_bg, (toggle_x, toggle_y, toggle_size, 35), border_radius=17)
                
                toggle_pos = toggle_x + (toggle_size - 28) if value else toggle_x + 4
                toggle_color = (240, 240, 240)
                pygame.draw.circle(screen, toggle_color, (int(toggle_pos + 14), toggle_y + 17), 14)
                
                status_text = "ON" if value else "OFF"
                status_color = (0, 255, 100) if value else (180, 180, 180)
                status_surf = self.font.render(status_text, True, status_color)
                status_x = toggle_x - 85
                screen.blit(status_surf, (status_x, y_offset + 35))
            else:
                if is_editing:
                    value_text = self.input_text if self.input_text else f"{value:.2f}"
                else:
                    value_text = f"{value:.2f}"
                value_color = (255, 255, 255)
                
                value_surf = self.font.render(value_text, True, value_color)
                value_x = modal_x + modal_width - 70 - value_surf.get_width()
                screen.blit(value_surf, (value_x, y_offset + 18))
                
                if value_range and i in [1, 2]:
                    slider_x = modal_x + 65
                    slider_y = y_offset + 55
                    slider_width = modal_width - 130
                    slider_height = 14
                    
                    min_val, max_val = value_range
                    ratio = (value - min_val) / (max_val - min_val)
                    slider_pos = slider_x + ratio * slider_width
                    
                    pygame.draw.rect(screen, (40, 40, 40), (slider_x, slider_y, slider_width, slider_height), border_radius=5)
                    filled_width = ratio * slider_width
                    if i == 1:
                        gradient_color = (255, int(120 + ratio * 135), int(120 + ratio * 135))
                    else:
                        gradient_color = (int(120 + ratio * 135), int(120 + ratio * 135), 255)
                    pygame.draw.rect(screen, gradient_color, (slider_x, slider_y, filled_width, slider_height), border_radius=5)
                    
                    handle_size = 18
                    handle_color = (220, 220, 220) if not (self.slider_dragging and self.slider_drag_field == i) else (255, 255, 100)
                    handle_y = slider_y + slider_height // 2
                    pygame.draw.circle(screen, handle_color, (int(slider_pos), handle_y), handle_size // 2)
                    pygame.draw.circle(screen, (60, 60, 60), (int(slider_pos), handle_y), handle_size // 2, 2)
            
            y_offset += line_height
        
        preview_y = actual_modal_y + modal_height - 110
        preview_text = f"Preview: {'Ativo' if self.temp_enabled else 'Inativo'}"
        preview_surf = self.font.render(preview_text, True, (150, 200, 255))
        screen.blit(preview_surf, (modal_x + 65, preview_y))
        
        help_lines = [
            "←/→: Ajustar  |  ↑/↓: Navegar  |  Enter: Aplicar  |  ESC: Fechar",
            "Clique e arraste nos sliders para ajustar valores"
        ]
        
        help_start_y = actual_modal_y + modal_height - 70
        for i, text in enumerate(help_lines):
            help_surf = self.font.render(text, True, (140, 140, 140))
            help_x = modal_x + (modal_width - help_surf.get_width()) // 2
            help_y = help_start_y + i * 28
            if help_y + 28 <= actual_modal_y + modal_height - 15:
                screen.blit(help_surf, (help_x, help_y))
