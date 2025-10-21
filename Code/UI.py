import pygame
import sys
import time
import random 

# Import các lớp logic và AI từ các tệp khác
from Game import Minesweeper, Gamestates
from AI import AI


# HẰNG SỐ VÀ CÀI ĐẶT
SETTINGS = {'width': 16, 'height': 16, 'mines': 40}
HEADER_HEIGHT = 60
COLOR_BG=(192,192,192); COLOR_GRID=(128,128,128); COLOR_REVEALED=(210,210,210); COLOR_HEADER=(50,50,50)
COLOR_WHITE=(255,255,255); COLOR_BLACK=(0,0,0); COLOR_RED=(255,0,0); COLOR_YELLOW=(255,255,0); COLOR_GREEN_LIME=(50,205,50)
NUMBER_COLORS={1:(0,0,255), 2:(0,128,0), 3:(255,0,0), 4:(0,0,128), 5:(128,0,0), 6:(0,128,128), 7:(0,0,0), 8:(128,128,128)}

# =================================================================================
# PHẦN 2: GIAO DIỆN PYGAME (Renderer)
# =================================================================================

class PygameRenderer:
    def __init__(self, settings):
        pygame.init()
        self.settings = settings
        self.cell_size = self._calculate_cell_size()
        
        min_width = 700 
        self.width = max(self.settings['width'] * self.cell_size, min_width)
        
        self.height = self.settings['height'] * self.cell_size + HEADER_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dò Mìn")
        self.game_logic = Minesweeper(settings['width'], settings['height'], settings['mines'])
        self.ai_logic = AI(settings['height'], settings['width'])
        self.start_time = None; self.elapsed_time = 0; self.should_return_to_menu = False; self.auto_play = False
        
        # SỬA LỖI FONT: Tách font cho Chữ và font cho Emoji
        text_font_names = ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif']
        emoji_font_names = ['Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Segoe UI Symbol', 'Symbola']

        # Font cho các ô (số, mìn, cờ)
        self.cell_emoji_font = find_font(emoji_font_names, int(self.cell_size * 0.7), bold=True)
        self.cell_number_font = find_font(text_font_names, int(self.cell_size * 0.7), bold=True)
        
        # Font cho Header
        self.header_text_font = find_font(text_font_names, 30, bold=True) # Dùng cho số (thời gian, mìn)
        self.header_emoji_font = find_font(emoji_font_names, 30, bold=True) # Dùng cho mặt cười
        self.menu_button_font = find_font(text_font_names, 18, bold=True) # Nút Menu, AI

        # Font cho thông báo
        self.message_font = find_font(text_font_names, 60, bold=True) # Thắng/Thua
        
        self.mine_text_rect = pygame.Rect(20, HEADER_HEIGHT // 2 - 15, 60, 30)
        self.reset_btn_rect = pygame.Rect(self.width // 2 - 25, HEADER_HEIGHT // 2 - 25, 50, 50)
        self.time_text_rect = pygame.Rect(self.width - 170, HEADER_HEIGHT // 2 - 15, 60, 30)
        self.menu_btn_rect = pygame.Rect(self.width - 95, HEADER_HEIGHT // 2 - 15, 80, 30)
        self.ai_hint_btn_rect = pygame.Rect(0, 0, 90, 30)
        self.auto_play_btn_rect = pygame.Rect(0, 0, 100, 30)

    def _calculate_cell_size(self):
        try:
            info = pygame.display.Info()
            max_w = (info.current_w - 50) // self.settings['width']
            max_h = (info.current_h - HEADER_HEIGHT - 100) // self.settings['height']
            return min(max_w, max_h, 40)
        except pygame.error: return 30

    def run_game(self):
        running = True
        while running and not self.should_return_to_menu:
            if self.auto_play and self.game_logic.gamestate == Gamestates.PLAYING:
                self._make_ai_move()
                pygame.time.wait(100)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    running = False 
                if event.type == pygame.MOUSEBUTTONDOWN: self._handle_click(event.pos, event.button)
            if self.start_time and self.game_logic.gamestate == Gamestates.PLAYING: self.elapsed_time = int(time.time() - self.start_time)
            self._draw_all()

    def _update_ai_from_game_state(self):
        """Đồng bộ AI với tất cả các ô đã mở mà AI chưa biết."""
        for cell in self.game_logic.revealed:
            if cell not in self.ai_logic.moves:
                self.ai_logic.add_knowledge(cell, self.game_logic.nearby_mines(cell), self.game_logic.get_neighbours(cell))

    def _make_ai_move(self):
        if self.start_time is None and self.game_logic.gamestate == Gamestates.PLAYING: self.start_time = time.time()
        self._update_ai_from_game_state() 
        for mine in self.ai_logic.mines:
            if not self.game_logic.is_flagged(mine): self.game_logic.change_flag(mine)
        move = self.ai_logic.make_safe_move()
        if move is None: move = self.ai_logic.make_random_move()
        if move is not None:
            self.game_logic.make_move(move)
            if not self.game_logic.is_lost():
                self._update_ai_from_game_state() 
        else: self.auto_play = False; print("AI: Không còn nước đi nào.")

    def _handle_click(self, pos, button):
        if button == 1:
            if self.menu_btn_rect.collidepoint(pos): self.should_return_to_menu = True; return
            if self.reset_btn_rect.collidepoint(pos): self.reset_game(); return
            if self.ai_hint_btn_rect.collidepoint(pos) and self.game_logic.gamestate == Gamestates.PLAYING: self._make_ai_move(); return
            if self.auto_play_btn_rect.collidepoint(pos): self.auto_play = not self.auto_play; return
        
        if (self.game_logic.is_won() or self.game_logic.is_lost()) and button == 1:
             self.reset_game(); return

        x, y = pos
        if y < HEADER_HEIGHT: return
        
        row, col = (y - HEADER_HEIGHT) // self.cell_size, x // self.cell_size
        square = (row, col)

        if not (0 <= row < self.settings['height'] and 0 <= col < self.settings['width']): return
        if self.start_time is None and self.game_logic.gamestate == Gamestates.PLAYING: self.start_time = time.time()
        
        if button == 1:
            self.game_logic.make_move(square)
            if not self.game_logic.is_lost():
                self._update_ai_from_game_state()
        elif button == 3:
            self.game_logic.change_flag(square)

    def reset_game(self):
        self.game_logic.reset(self.settings['width'], self.settings['height'], self.settings['mines'])
        self.ai_logic.reset()
        self.start_time = None; self.elapsed_time = 0; self.auto_play = False

    def _draw_all(self):
        self.screen.fill(COLOR_BG)
        self._draw_header()
        self._draw_board()
        if self.game_logic.is_won() or self.game_logic.is_lost():
            self.auto_play = False
            self._draw_game_over_message()
        pygame.display.flip()

    def _draw_header(self):
        pygame.draw.rect(self.screen, COLOR_HEADER, (0, 0, self.width, HEADER_HEIGHT))
        
        # Cờ
        mines_left = self.game_logic.minecount - len(self.game_logic.flags)
        mine_text = self.header_text_font.render(f"{mines_left:03d}", True, COLOR_RED)
        self.mine_text_rect = mine_text.get_rect(topleft=(20, HEADER_HEIGHT // 2 - mine_text.get_height() // 2))
        self.screen.blit(mine_text, self.mine_text_rect)
        
        # Nút Reset (Mặt cười)
        face = "🙂";
        if self.game_logic.is_won(): face = "😎"
        if self.game_logic.is_lost(): face = "😵"
        pygame.draw.rect(self.screen, COLOR_YELLOW, self.reset_btn_rect); pygame.draw.rect(self.screen, COLOR_BLACK, self.reset_btn_rect, 2)
        face_surf = self.header_emoji_font.render(face, True, COLOR_BLACK); face_rect = face_surf.get_rect(center=self.reset_btn_rect.center); self.screen.blit(face_surf, face_rect)
        
        # Nút Menu - dùng menu_button_font
        pygame.draw.rect(self.screen, COLOR_GRID, self.menu_btn_rect); pygame.draw.rect(self.screen, COLOR_WHITE, self.menu_btn_rect, 2)
        menu_text_surf = self.menu_button_font.render("MENU", True, COLOR_WHITE)
        menu_text_rect = menu_text_surf.get_rect(center=self.menu_btn_rect.center)
        self.screen.blit(menu_text_surf, menu_text_rect)
        
        # Đồng hồ - SỬA: dùng header_text_font
        time_text = self.header_text_font.render(f"{self.elapsed_time:03d}", True, COLOR_RED)
        self.time_text_rect = time_text.get_rect(topright=(self.menu_btn_rect.left - 15, HEADER_HEIGHT // 2 - time_text.get_height() // 2))
        self.screen.blit(time_text, self.time_text_rect)

        # Nút Gợi ý - dùng menu_button_font
        self.ai_hint_btn_rect.topleft = (self.mine_text_rect.right + 20, HEADER_HEIGHT//2 - 15)
        pygame.draw.rect(self.screen, COLOR_GRID, self.ai_hint_btn_rect); pygame.draw.rect(self.screen, COLOR_WHITE, self.ai_hint_btn_rect, 2)
        ai_text = self.menu_button_font.render("Gợi Ý", True, COLOR_WHITE)
        self.screen.blit(ai_text, ai_text.get_rect(center=self.ai_hint_btn_rect.center))
        
        # Nút Tự động - dùng menu_button_font
        self.auto_play_btn_rect.topleft = (self.ai_hint_btn_rect.right + 10, HEADER_HEIGHT // 2 - 15)
        auto_play_color = COLOR_GREEN_LIME if self.auto_play else COLOR_RED
        auto_play_text = "DỪNG" if self.auto_play else "Sử dụng AI"
        pygame.draw.rect(self.screen, auto_play_color, self.auto_play_btn_rect); pygame.draw.rect(self.screen, COLOR_WHITE, self.auto_play_btn_rect, 2)
        auto_text = self.menu_button_font.render(auto_play_text, True, COLOR_WHITE)
        self.screen.blit(auto_text, auto_text.get_rect(center=self.auto_play_btn_rect.center))


    def _draw_board(self):
        for r in range(self.settings['height']):
            for c in range(self.settings['width']):
                rect = pygame.Rect(c*self.cell_size, r*self.cell_size + HEADER_HEIGHT, self.cell_size, self.cell_size)
                square = (r, c)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
                if self.game_logic.is_visible(square):
                    pygame.draw.rect(self.screen, COLOR_REVEALED, rect)
                    if self.game_logic.is_mine(square):
                        # SỬA: dùng cell_emoji_font
                        surf = self.cell_emoji_font.render('💣', True, COLOR_BLACK); s_rect = surf.get_rect(center=rect.center); self.screen.blit(surf, s_rect)
                        if self.game_logic.is_lost(): s = pygame.Surface((self.cell_size, self.cell_size)); s.set_alpha(100); s.fill(COLOR_RED); self.screen.blit(s, rect.topleft)
                    else:
                        nearby = self.game_logic.nearby_mines(square)
                        if nearby > 0: 
                            color = NUMBER_COLORS.get(nearby, COLOR_BLACK)
                            # SỬA: dùng cell_number_font
                            surf = self.cell_number_font.render(str(nearby), True, color); s_rect = surf.get_rect(center=rect.center); self.screen.blit(surf, s_rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_BG, rect); lw = max(1, int(self.cell_size * 0.08))
                    pygame.draw.line(self.screen, COLOR_WHITE, rect.topleft, (rect.right-lw, rect.top), lw); pygame.draw.line(self.screen, COLOR_WHITE, rect.topleft, (rect.left, rect.bottom-lw), lw)
                    pygame.draw.line(self.screen, COLOR_GRID, (rect.right-lw, rect.top), (rect.right-lw, rect.bottom-lw), lw); pygame.draw.line(self.screen, COLOR_GRID, (rect.left, rect.bottom-lw), (rect.right-lw, rect.bottom-lw), lw)
                    # SỬA: dùng cell_emoji_font
                    if self.game_logic.is_flagged(square): surf = self.cell_emoji_font.render('🚩', True, COLOR_RED); s_rect = surf.get_rect(center=rect.center); self.screen.blit(surf, s_rect)
                if self.game_logic.is_lost():
                    # SỬA: dùng cell_emoji_font
                    if self.game_logic.is_mine(square) and not self.game_logic.is_flagged(square): surf = self.cell_emoji_font.render('💣', True, COLOR_BLACK); s_rect = surf.get_rect(center=rect.center); self.screen.blit(surf, s_rect)
                    # SỬA: dùng cell_emoji_font
                    if not self.game_logic.is_mine(square) and self.game_logic.is_flagged(square): surf = self.cell_emoji_font.render('❌', True, COLOR_RED); s_rect = surf.get_rect(center=rect.center); self.screen.blit(surf, s_rect)

    def _draw_game_over_message(self):
        message = "BẠN ĐÃ THẮNG!" if self.game_logic.is_won() else "BẠN ĐÃ THUA!"
        color = COLOR_GREEN_LIME if self.game_logic.is_won() else COLOR_RED
        overlay = pygame.Surface((self.width, self.height - HEADER_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); self.screen.blit(overlay, (0, HEADER_HEIGHT))
        text_surf = self.message_font.render(message, True, color); text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2 + HEADER_HEIGHT // 2)); self.screen.blit(text_surf, text_rect)

# Tìm font hợp lệ
def find_font(font_names, size, bold=False, italic=False):
    """
    Thử tìm một font hệ thống hợp lệ từ danh sách tên font.
    Trả về font mặc định của Pygame nếu không tìm thấy.
    """
    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size, bold=bold, italic=italic)
            # Thử render để chắc chắn nó không phải là font rỗng
            font.render("test", True, (0,0,0)) 
            print(f"Sử dụng font: {name} (size {size})")
            return font
        except Exception as e: 
            continue
    
    # Nếu không tìm thấy font nào, dùng font mặc định
    print(f"Cảnh báo: Không tìm thấy font nào trong {font_names}. Dùng font mặc định.")
    return pygame.font.Font(None, size) # Font mặc định

# MENU CÀI ĐẶT
DIFFICULTY_PRESETS = {
    'easy': {'width': 8, 'height': 8, 'mines': 10},
    'medium': {'width': 16, 'height': 16, 'mines': 40},
    'hard': {'width': 30, 'height': 16, 'mines': 100}
}

def draw_arrow_button(screen, rect, direction='up', is_hover=False):
    bg_color = COLOR_YELLOW if is_hover else COLOR_BG; pygame.draw.rect(screen, bg_color, rect); pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
    if direction == 'up': points = [(rect.centerx, rect.top+rect.height*0.3), (rect.left+rect.width*0.3, rect.bottom-rect.height*0.3), (rect.right-rect.width*0.3, rect.bottom-rect.height*0.3)]
    else: points = [(rect.centerx, rect.bottom-rect.height*0.3), (rect.left+rect.width*0.3, rect.top+rect.height*0.3), (rect.right-rect.width*0.3, rect.top+rect.height*0.3)]
    pygame.draw.polygon(screen, COLOR_BLACK, points)

def run_settings_menu():
    """
    Hiển thị menu cài đặt.
    Hàm này tự khởi tạo và đóng pygame.
    Trả về True nếu người dùng chọn "BẮT ĐẦU",
    Trả về False nếu người dùng đóng cửa sổ hoặc chọn "THOÁT".
    """
    global SETTINGS # Hàm này sẽ sửa đổi SETTINGS toàn cục
    pygame.init()
    width, height = 500, 520
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Cài đặt Dò Mìn")
    
    # SỬA LỖI FONT: Dùng hàm find_font
    text_font_names = ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif']
    font_title = find_font(text_font_names, 40, bold=True)
    font_text = find_font(text_font_names, 28)
    font_small = find_font(text_font_names, 22)
    
    clock = pygame.time.Clock()
    
    preset_btn_w, preset_btn_h = 120, 40
    preset_y = 100
    preset_buttons = {
        'easy': pygame.Rect(width//2 - preset_btn_w*1.5 - 10, preset_y, preset_btn_w, preset_btn_h),
        'medium': pygame.Rect(width//2 - preset_btn_w*0.5, preset_y, preset_btn_w, preset_btn_h),
        'hard': pygame.Rect(width//2 + preset_btn_w*0.5 + 10, preset_y, preset_btn_w, preset_btn_h)
    }
    
    button_rects = {}; btn_w, btn_h, btn_x = 40, 20, 380
    y_pos = {'width': 220, 'height': 270, 'mines': 320}
    for key in y_pos.keys():
        button_rects[f'{key}_up'] = pygame.Rect(btn_x, y_pos[key], btn_w, btn_h)
        button_rects[f'{key}_down'] = pygame.Rect(btn_x, y_pos[key] + btn_h + 2, btn_w, btn_h)
    
    start_btn = pygame.Rect(width // 2 - 110, 420, 200, 50)
    exit_btn = pygame.Rect(width // 2 - 110, 475, 200, 35)
    
    running = True
    start_game = False
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                start_game = False # Thoát
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_btn.collidepoint(mouse_pos):
                    running = False
                    start_game = True # Bắt đầu
                if exit_btn.collidepoint(mouse_pos):
                    running = False
                    start_game = False # Thoát

                for mode, rect in preset_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        SETTINGS.clear()
                        SETTINGS.update(DIFFICULTY_PRESETS[mode])
                
                for key, rect in button_rects.items():
                    if rect.collidepoint(mouse_pos):
                        setting, direction = key.split('_'); change = 1 if 'up' in direction else -1
                        SETTINGS[setting] += change
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT: SETTINGS[setting] += change * 9
        
        SETTINGS['width'] = max(8, min(100, SETTINGS['width'])); 
        SETTINGS['height'] = max(8, min(100, SETTINGS['height']))
        max_mines = (SETTINGS['width'] * SETTINGS['height']) - 9; 
        SETTINGS['mines'] = max(1, min(max_mines, SETTINGS['mines']))
        
        screen.fill(COLOR_BLACK)
        title = font_title.render("Chọn Chế Độ", True, COLOR_WHITE); screen.blit(title, (width//2 - title.get_width()//2, 20))

        for mode, rect in preset_buttons.items():
            is_hover = rect.collidepoint(mouse_pos)
            is_active = (SETTINGS['width'] == DIFFICULTY_PRESETS[mode]['width'] and
                         SETTINGS['height'] == DIFFICULTY_PRESETS[mode]['height'] and
                         SETTINGS['mines'] == DIFFICULTY_PRESETS[mode]['mines'])
            
            bg_color = COLOR_YELLOW if is_hover else (COLOR_GREEN_LIME if is_active else COLOR_BG)
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
            
            mode_text = mode.capitalize()
            if mode == 'easy': mode_text = "Dễ"
            elif mode == 'medium': mode_text = "Trung bình"
            elif mode == 'hard': mode_text = "Khó"
            
            text_surf = font_small.render(mode_text, True, COLOR_BLACK if is_active or is_hover else COLOR_WHITE)
            screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        custom_title = font_text.render("--- Hoặc Tùy Chỉnh ---", True, COLOR_GRID); screen.blit(custom_title, (width//2 - custom_title.get_width()//2, 170))
        
        text_w = font_text.render(f"Chiều Rộng: {SETTINGS['width']}", True, COLOR_WHITE); screen.blit(text_w, (50, y_pos['width']+10))
        text_h = font_text.render(f"Chiều Cao: {SETTINGS['height']}", True, COLOR_WHITE); screen.blit(text_h, (50, y_pos['height']+10))
        text_m = font_text.render(f"Số Mìn: {SETTINGS['mines']}", True, COLOR_WHITE); screen.blit(text_m, (50, y_pos['mines']+10))
        for key, rect in button_rects.items(): draw_arrow_button(screen, rect, 'up' if 'up' in key else 'down', rect.collidepoint(mouse_pos))
        
        start_bg = COLOR_YELLOW if start_btn.collidepoint(mouse_pos) else COLOR_GREEN_LIME; pygame.draw.rect(screen, start_bg, start_btn)
        start_text = font_text.render("BẮT ĐẦU", True, COLOR_BLACK); screen.blit(start_text, (start_btn.centerx-start_text.get_width()//2, start_btn.centery-start_text.get_height()//2))
        exit_bg = COLOR_YELLOW if exit_btn.collidepoint(mouse_pos) else COLOR_RED; pygame.draw.rect(screen, exit_bg, exit_btn)
        exit_text = font_text.render("THOÁT", True, COLOR_WHITE); screen.blit(exit_text, (exit_btn.centerx-exit_text.get_width()//2, exit_btn.centery-exit_text.get_height()//2))
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    return start_game