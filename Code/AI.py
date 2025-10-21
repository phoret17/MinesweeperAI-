
import random
from copy import deepcopy

class Statement:
    """
    Đại diện cho một "câu" logic, ví dụ:
    "Trong 3 ô {A, B, C} có đúng 1 quả mìn."
    """
    def __init__(self, cells, count):
        # self.cells = tập hợp các ô chưa biết (ví dụ: {A, B, C})
        self.cells = set(cells)
        # self.count = số lượng mìn trong các ô đó (ví dụ: 1)
        self.count = count

    def __eq__(self, other):
        """Kiểm tra xem hai câu logic có giống hệt nhau không."""
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        """Biểu diễn câu logic dưới dạng chuỗi để gỡ lỗi (debug)."""
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Trả về tất cả các ô là mìn, nếu suy luận được.
        Ví dụ: 3 ô = 3 mìn -> tất cả 3 ô đều là mìn.
        """
        return self.cells if self.count == len(self.cells) else set()

    def known_safes(self):
        """
        Trả về tất cả các ô an toàn, nếu suy luận được.
        Ví dụ: 3 ô = 0 mìn -> tất cả 3 ô đều an toàn.
        """
        return self.cells if self.count == 0 else set()

    def mark_mine(self, cell):
        """
        Nếu 'cell' nằm trong câu này, hãy loại bỏ nó và giảm
        số lượng mìn (count) đi 1.
        """
        if cell in self.cells:
            self.count -= 1
            self.cells.remove(cell)

    def mark_safe(self, cell):
        """
        Nếu 'cell' nằm trong câu này, hãy loại bỏ nó.
        Số lượng mìn (count) không đổi.
        """
        if cell in self.cells:
            self.cells.remove(cell)

class AI:
    """Lớp AI chính để giải game Dò Mìn."""
    def __init__(self, height, width):
        self.height = height
        self.width = width
        # self.knowledge: Danh sách các câu logic (Statement) mà AI biết.
        self.knowledge = []
        # self.moves: Tập hợp các ô đã được nhấp (lật)
        self.moves = set()
        # self.mines: Tập hợp các ô được xác định chắc chắn là mìn.
        self.mines = set()
        # self.safes: Tập hợp các ô được xác định chắc chắn là an toàn.
        self.safes = set()

    def mark_mine(self, cell):
        """Đánh dấu một ô là mìn và cập nhật toàn bộ cơ sở tri thức."""
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """Đánh dấu một ô là an toàn và cập nhật toàn bộ cơ sở tri thức."""
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count, neighbours):
        """
        Hàm chính: Thêm thông tin mới khi một ô được lật.
        cell: (hàng, cột) của ô vừa lật.
        count: Số mìn xung quanh ô 'cell'.
        neighbours: Danh sách các ô hàng xóm của 'cell'.
        """
        # 1. Đánh dấu ô vừa lật là đã di chuyển và an toàn.
        self.moves.add(cell)
        self.mark_safe(cell)

        # 2. Lọc các hàng xóm:
        # Chỉ giữ lại các ô chưa biết (không nằm trong safes hoặc mines).
        unknown_neighbours = []
        known_mines_count = 0
        for neighbour in neighbours:
            if neighbour in self.mines:
                known_mines_count += 1
            elif neighbour not in self.safes:
                unknown_neighbours.append(neighbour)
        
        # 3. Tạo câu logic mới từ các ô hàng xóm chưa biết
        # và số mìn còn lại.
        new_statement = Statement(unknown_neighbours, count - known_mines_count)
        
        # 4. Thêm câu mới vào cơ sở tri thức (nếu nó chưa tồn tại)
        if new_statement not in self.knowledge:
            self.knowledge.append(new_statement)
        
        # 5. Suy luận từ tri thức mới
        self.infer_knowledge()
        
        # 6. Dọn dẹp các câu logic rỗng
        self.cleanup_knowledge()

    def infer_knowledge(self):
        """
        Hàm suy luận logic. Lặp lại cho đến khi không thể
        suy luận thêm bất kỳ thông tin mới nào.
        """
        new_knowledge_found = True
        while new_knowledge_found:
            new_knowledge_found = False
            
            # --- Bước 1: Suy luận đơn giản (0 mìn hoặc N mìn) ---
            safes_found = set()
            mines_found = set()
            
            for sentence in self.knowledge:
                safes_found.update(sentence.known_safes())
                mines_found.update(sentence.known_mines())
            
            # Cập nhật tri thức nếu tìm thấy ô an toàn mới
            if safes_found:
                for safe in safes_found:
                    if safe not in self.safes:
                        self.mark_safe(safe)
                        new_knowledge_found = True # Đánh dấu để lặp lại
            
            # Cập nhật tri thức nếu tìm thấy mìn mới
            if mines_found:
                for mine in mines_found:
                    if mine not in self.mines:
                        self.mark_mine(mine)
                        new_knowledge_found = True # Đánh dấu để lặp lại

            # --- Bước 2: Suy luận tập hợp con (Nâng cao) ---
            # Ví dụ: S1 = {A, B} = 1 mìn
            #        S2 = {A, B, C} = 2 mìn
            # Suy ra: S3 = (S2 - S1) = {C} = (2 - 1) = 1 mìn -> C là mìn.
            knowledge_copy = deepcopy(self.knowledge)
            for s1 in knowledge_copy:
                for s2 in knowledge_copy:
                    # Nếu s1 là tập con của s2
                    if s1.cells.issubset(s2.cells) and s1 != s2:
                        inferred_cells = s2.cells - s1.cells
                        inferred_count = s2.count - s1.count
                        
                        # Tạo câu logic mới từ suy luận
                        inferred_statement = Statement(inferred_cells, inferred_count)
                        
                        # Thêm vào tri thức nếu nó mới
                        if inferred_statement not in self.knowledge:
                            self.knowledge.append(inferred_statement)
                            new_knowledge_found = True # Đánh dấu để lặp lại

    def cleanup_knowledge(self):
        """Loại bỏ các câu logic rỗng (ví dụ: {} = 0) ra khỏi tri thức."""
        self.knowledge = [s for s in self.knowledge if s.cells]

    def make_safe_move(self):
        """
        Tìm một nước đi an toàn đã biết.
        Ưu tiên hàng đầu của AI.
        """
        # Tìm một ô trong 'safes' mà chưa được 'moves' (chưa lật)
        safe_moves = self.safes - self.moves
        return safe_moves.pop() if safe_moves else None

    def make_random_move(self):
        """
        Nếu không còn nước đi an toàn nào, AI phải đoán.
        Chọn một ô ngẫu nhiên không phải là mìn đã biết
        và chưa được lật.
        """
        pickable_cells = []
        for i in range(self.height):
            for j in range(self.width):
                cell = (i, j)
                if cell not in self.moves and cell not in self.mines:
                    pickable_cells.append(cell)
        
        return random.choice(pickable_cells) if pickable_cells else None

    def reset(self):
        """Xóa toàn bộ tri thức để bắt đầu game mới."""
        self.knowledge = []
        self.moves = set()
        self.mines = set()
        self.safes = set()