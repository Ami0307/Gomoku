from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE, MARGIN, get_screen, get_screen_size, bgm_enabled, sound_enabled, toggle_bgm, toggle_sound, play_bgm, stop_bgm, move_sound, get_bgm_enabled,get_move_sound
from ui import main_menu, game_mode_selection, network_mode_selection, show_winner_popup, draw_stones, show_available_rooms, waiting_room, draw_game_screen, choose_first_player
from network import start_network_game
from ai import ai_move
import pygame
import sys
import time
import threading
WHITE = (255, 255, 255)

def start_game_ui():
    """启动游戏 UI，包括主菜单和模式选择"""
    game_mode = main_menu()
    if game_mode == "local":
        mode = game_mode_selection()
        if mode == "AI":
            first_player = choose_first_player()
            return mode, None, None, first_player
        return mode, None, None, None
    elif game_mode == "network":
        network_mode, port = network_mode_selection()  # 获取 port
        if network_mode == "back":
            return start_game_ui()
        if network_mode == "server":
            return "Player", network_mode, port, None  # 使用已获取的 port
        else:
            host, port = show_available_rooms()
            return "Player", "client", (host, port), None
    else:
        return None, None, None, None

def play_game(game, mode, network_mode=None, port=None, first_player=None):
    """实际的游戏循环"""
    global bgm_enabled
    screen = get_screen()
    pygame.display.set_caption("五子棋")

    network = None
    if network_mode:
        network, game = start_network_game(game, network_mode, port=port)
        if not network:
            return "main_menu"
        network = waiting_room(is_host=(network_mode == "server"), network=network)
        if not network or network == "main_menu":
            return "main_menu"
        
        network.stop_receive_thread()
        network.start_server_receive_thread()
        
        game.player_color = 'Black' if network_mode == "server" else 'White'

    clock = pygame.time.Clock()

    if mode == "AI" and first_player == "AI":
        draw_game_screen(screen, game, network_mode is not None)
        pygame.time.wait(500)
        ai_move(game) 

    try:
        while True:
            main_menu_button, undo_button, board_start_x, board_start_y, grid_size, bgm_checkbox_rect = draw_game_screen(screen, game, network_mode is not None)

            if game.is_over():
                winner = game.get_winner()
                action = show_winner_popup(screen, winner)
                if network:
                    network.close()
                return action

            if network_mode:
                move_data = network.check_network_data()
                if move_data:
                    if isinstance(move_data, dict) and move_data.get("type") == "undo_request":
                        # 收到撤回请求时，双方同时撤回两步
                        game.undo_move(2)  # 撤回两步
                    elif isinstance(move_data, list) and len(move_data) == 2:
                        row, col = move_data
                        if game.is_valid_move(row, col):
                            game.update_board(row, col)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if main_menu_button.collidepoint(event.pos):
                        return "main_menu"
                    elif undo_button.collidepoint(event.pos):
                        if network_mode:
                            if game.is_player_turn(game.player_color):
                                # 在网络模式下，发送撤回请求并立即撤回自己的两步
                                network.send({"type": "undo_request"})
                                game.undo_move(2)  # 本地也撤回两步
                        else:
                            # 本地模式
                            steps = 2 if mode == "AI" else 1
                            game.undo_move(steps)
                    elif bgm_checkbox_rect.collidepoint(x, y):
                        bgm_enabled = toggle_bgm()
                        # 只重绘菜单栏区域
                        main_menu_button, _, _, _, _, bgm_checkbox_rect = draw_game_screen(screen, game, network_mode is not None)
                        pygame.display.update(pygame.Rect(0, 0, screen.get_width(), 40))  # 假设菜单栏高度为 40 像素
                    else:
                        #x, y = event.pos
                        col = round((x - board_start_x) / grid_size)
                        row = round((y - board_start_y) / grid_size)
                        
                        if game.is_valid_move(row, col):
                            if network_mode:
                                if game.is_player_turn(game.player_color):
                                    if game.update_board(row, col):
                                        if get_move_sound():
                                            move_sound.play()
                                        network.send_move(row, col)
                                else:
                                    print("现在不是你的回合！")
                            else:  # 本地模式（玩家对战或AI对战）
                                if game.update_board(row, col):
                                    if get_move_sound():
                                        move_sound.play()
                                    if mode == "AI":
                                        draw_game_screen(screen, game, network_mode is not None)
                                        pygame.display.flip()
                                        if get_move_sound():
                                            move_sound.play()
                                        pygame.time.wait(500)
                                        ai_move(game)

            pygame.display.flip()
            clock.tick(30)

    finally:
        if network:
            print("Closing network connection")
            network.close()

def print_bgm_status():
    while True:
        print(get_bgm_enabled(),get_move_sound())
        time.sleep(1)

def game_loop():
    """游戏主循环"""
    # 启动打印 BGM 状态的线程
    bgm_status_thread = threading.Thread(target=print_bgm_status, daemon=True)
    bgm_status_thread.start()

    while True:
        game = Game()
        mode, network_mode, port, first_player = start_game_ui()
        if mode is None:
            break
        
        while True:
            action = play_game(game, mode, network_mode, port, first_player)
            if action == "quit":
                return
            elif action == "main_menu":
                break
            elif action == "play_again":
                game = Game()
                continue
        
        if action == "quit":
            break

    # 主线程结束时，daemon 线程会自动结束，无需手动停止

if __name__ == "__main__":
    game_loop()
