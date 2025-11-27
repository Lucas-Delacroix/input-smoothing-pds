from typing import Optional, Tuple
import pygame

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
        
    def open(self) -> None:
        self.active = True
        self.temp_enabled = self.tremor_sim.enabled
        self.temp_intensity = self.tremor_sim.intensity
        self.temp_frequency = self.tremor_sim.frequency
        self.selected_field = 0
        self.editing_field = False
        self.input_text = ""
        
    def close(self) -> None:
        self.active = False
        self.editing_field = False
        self.input_text = ""
        
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
                else:
                    self.editing_field = True
                    if self.selected_field == 1:
                        self.input_text = str(self.temp_intensity)
                    elif self.selected_field == 2:
                        self.input_text = str(self.temp_frequency)
                return True
                
        return False
        
    def _apply_input(self) -> None:
        try:
            value = float(self.input_text)
            if self.selected_field == 1:
                self.temp_intensity = max(0.0, value)
            elif self.selected_field == 2:
                self.temp_frequency = max(0.1, value)
        except ValueError:
            pass
        self.editing_field = False
        self.input_text = ""
        
    def _apply_changes(self) -> None:
        self.tremor_sim.set_enabled(self.temp_enabled)
        self.tremor_sim.set_intensity(self.temp_intensity)
        self.tremor_sim.set_frequency(self.temp_frequency)
        
    def render(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        screen_width, screen_height = screen.get_size()
        modal_width = 500
        modal_height = 300
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(screen, (40, 40, 40), (modal_x, modal_y, modal_width, modal_height))
        pygame.draw.rect(screen, (100, 100, 100), (modal_x, modal_y, modal_width, modal_height), 2)
        
        title = self.font.render("Configuração de Tremor", True, (255, 255, 255))
        title_rect = title.get_rect(center=(modal_x + modal_width // 2, modal_y + 30))
        screen.blit(title, title_rect)
        
        y_offset = modal_y + 70
        line_height = 50
        
        fields = [
            ("Ativar Tremor", self.temp_enabled, "bool"),
            ("Intensidade", self.temp_intensity, "float"),
            ("Frequência (Hz)", self.temp_frequency, "float"),
        ]
        
        for i, (label, value, field_type) in enumerate(fields):
            is_selected = i == self.selected_field
            is_editing = is_selected and self.editing_field
            
            bg_color = (60, 60, 60) if is_selected else (50, 50, 50)
            pygame.draw.rect(screen, bg_color, (modal_x + 20, y_offset, modal_width - 40, 40))
            
            if is_selected:
                pygame.draw.rect(screen, (100, 150, 255), (modal_x + 20, y_offset, modal_width - 40, 40), 2)
            
            label_text = self.font.render(label + ":", True, (200, 200, 200))
            screen.blit(label_text, (modal_x + 30, y_offset + 10))
            
            if field_type == "bool":
                value_text = "ON" if value else "OFF"
                value_color = (0, 255, 0) if value else (255, 0, 0)
            else:
                if is_editing:
                    value_text = self.input_text if self.input_text else str(value)
                else:
                    value_text = f"{value:.2f}"
                value_color = (255, 255, 255)
            
            value_surf = self.font.render(value_text, True, value_color)
            value_x = modal_x + modal_width - 30 - value_surf.get_width()
            screen.blit(value_surf, (value_x, y_offset + 10))
            
            y_offset += line_height
        
        help_text = [
            "↑/↓: Navegar  |  Enter: Editar/Aplicar  |  ESC: Cancelar",
            "Espaço: Toggle (campo Ativar Tremor)"
        ]
        
        for i, text in enumerate(help_text):
            help_surf = self.font.render(text, True, (150, 150, 150))
            help_rect = help_surf.get_rect(center=(modal_x + modal_width // 2, modal_y + modal_height - 40 + i * 20))
            screen.blit(help_surf, help_rect)

