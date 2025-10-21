from enum import Enum
from random import randrange

class Gamestates(Enum):
    """Lưu trữ các trạng thái khác nhau của game (đang chơi, thắng, thua)."""
    PLAYING = 0
    WON = 1
    LOST = 2

class Minesweeper:
    """Lớp logic game Dò Mìn cơ bản."""
    def __init__(self, width, height, mines):
        """Khởi tạo bàn cờ với kích thước và số mìn."""
        self.width = width
        self.height = height
        self.minecount = mines
        self.flags = set()      # Tập hợp các ô đã cắm cờ (hàng, cột)
        self.mines = set()      # Tập hợp các ô có mìn thật sự
        self.revealed = set()   # Tập hợp các ô đã được lật mở
        self.gamestate = Gamestates.PLAYING  # Trạng thái game ban đầu

    def generate_mines(self, first_click_square):
        """Tạo mìn ngẫu nhiên, đảm bảo không trúng ô click đầu tiên."""
        mines_generated = 0
        while mines_generated < self.minecount:
            square = (randrange(self.height), randrange(self.width))
            # Bỏ qua nếu ô này đã có mìn, hoặc là ô click đầu tiên
            if square in self.mines or square == first_click_square:
                continue
            self.mines.add(square)
            mines_generated += 1

    def reset(self, width, height, mines):
        """Thiết lập lại game (chơi lại) với cài đặt mới hoặc cũ."""
        self.width = width
        self.height = height
        self.minecount = mines
        self.flags = set()
        self.mines = set()
        self.revealed = set()
        self.gamestate = Gamestates.PLAYING

    def make_move(self, square):
        """Xử lý khi người chơi click (lật) một ô."""
        # Không làm gì nếu ô không hợp lệ, đã cắm cờ, hoặc game đã kết thúc
        if square is None or square in self.flags or self.gamestate != Gamestates.PLAYING:
            return
        
        # Nếu đây là click đầu tiên, tạo mìn (tránh ô 'square')
        if not self.mines and self.minecount > 0:
            self.generate_mines(square)
            
        # Lật ô này
        self.revealed.add(square)
        
        # Trúng mìn -> Thua
        if square in self.mines:
            self.gamestate = Gamestates.LOST
            return
            
        # Nếu ô này là ô 0, lật các ô trống xung quanh (lan ra)
        if self.nearby_mines(square) == 0:
            self._reveal_empty_squares(square)
            
        # Nếu số ô đã lật = (tổng số ô - số mìn) -> Thắng
        if len(self.revealed) == self.width * self.height - self.minecount:
            self.gamestate = Gamestates.WON

    def _reveal_empty_squares(self, square):
        """Thuật toán loang (flood-fill) để tự động lật các ô 0 liền kề."""
        queue = [square]      # Hàng đợi các ô cần kiểm tra
        visited = {square}    # Các ô đã thêm vào hàng đợi (tránh lặp vô hạn)
        
        while queue:
            current_square = queue.pop(0)
            for neighbor in self.get_neighbours(current_square):
                # Chỉ xử lý nếu ô hàng xóm chưa được lật, chưa cắm cờ, và chưa thăm
                if neighbor not in visited and neighbor not in self.revealed and neighbor not in self.flags:
                    visited.add(neighbor)
                    self.revealed.add(neighbor) # Lật ô hàng xóm này
                    
                    # Nếu ô hàng xóm này cũng là ô 0, thêm nó vào hàng đợi để tiếp tục loang
                    if self.nearby_mines(neighbor) == 0:
                        queue.append(neighbor)

    def change_flag(self, square):
        """Xử lý khi người chơi click chuột phải (cắm/gỡ cờ)."""
        # Không cho cắm cờ nếu game đã kết thúc hoặc ô đã lật
        if self.gamestate != Gamestates.PLAYING or square in self.revealed:
            return
            
        if square in self.flags:
            self.flags.remove(square)  # Nếu đã có cờ -> gỡ cờ
        else:
            self.flags.add(square)     # Nếu chưa có cờ -> cắm cờ

    # --- Các hàm trợ giúp (getter) để kiểm tra trạng thái ---

    def is_lost(self): 
        """Kiểm tra xem đã thua chưa."""
        return self.gamestate == Gamestates.LOST
        
    def is_won(self): 
        """Kiểm tra xem đã thắng chưa."""
        return self.gamestate == Gamestates.WON
        
    def is_flagged(self, square): 
        """Kiểm tra ô (hàng, cột) có cờ không."""
        return square in self.flags
        
    def is_mine(self, square): 
        """Kiểm tra ô (hàng, cột) có mìn không."""
        return square in self.mines
        
    def is_visible(self, square): 
        """Kiểm tra ô (hàng, cột) đã lật chưa."""
        return square in self.revealed
        
    def nearby_mines(self, square): 
        """Đếm số mìn xung quanh ô (hàng, cột)."""
        return sum(1 for n in self.get_neighbours(square) if n in self.mines)
        
    def get_neighbours(self, square):
        """Lấy danh sách 8 ô hàng xóm hợp lệ xung quanh ô (hàng, cột)."""
        if square is None: 
            return []
            
        r, c = square
        neighbours = []
        for i in range(-1, 2):      # Duyệt 3 hàng (trên, giữa, dưới)
            for j in range(-1, 2):  # Duyệt 3 cột (trái, giữa, phải)
                if i == 0 and j == 0: 
                    continue  # Bỏ qua chính nó
                    
                nr, nc = r + i, c + j  # Tọa độ hàng xóm mới
                
                # Kiểm tra xem hàng xóm có nằm trong bàn cờ không
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    neighbours.append((nr, nc))
        return neighbours