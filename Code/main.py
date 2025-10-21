import pygame
from UI import run_settings_menu, PygameRenderer, SETTINGS

def main():
    while True:
        # 1. Chạy menu. Hàm này sẽ tự init, chạy và quit pygame.
        # Nó trả về True nếu nhấn "BẮT ĐẦU", False nếu nhấn "THOÁT".
        should_start_game = run_settings_menu()

        if not should_start_game:
            print("Thoát khỏi chương trình.")
            break
        
        # 2. Nếu 'should_start_game' là True, 'SETTINGS' đã được cập nhật.
        print(f"Bắt đầu game với cài đặt: {SETTINGS}")
        
        # Lớp PygameRenderer sẽ tự pygame.init() lại
        game_instance = PygameRenderer(SETTINGS)
        
        # 3. Chạy game. Vòng lặp này chạy cho đến khi người dùng
        # đóng cửa sổ game hoặc nhấn nút "MENU".
        game_instance.run_game()

        # 4. Sau khi game_instance.run_game() kết thúc, chúng ta PHẢI
        # gọi pygame.quit() để đóng cửa sổ game.
        pygame.quit()

        if not game_instance.should_return_to_menu:
            # Nếu người dùng không nhấn "MENU" (nghĩa là họ đã đóng cửa sổ)
            print("Đóng cửa sổ game, thoát chương trình.")
            break
        else:
            # Người dùng nhấn "MENU", quay lại vòng lặp
            print("Quay trở lại menu...")
            # Vòng lặp 'while True' sẽ tiếp tục, gọi lại run_settings_menu()

if __name__ == '__main__':
    main()