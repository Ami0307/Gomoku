from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE, MARGIN, get_screen, get_screen_size
from ui import main_menu, game_mode_selection, network_mode_selection, show_winner_popup, draw_stones, show_available_rooms, waiting_room, draw_game_screen, choose_first_player
from network import start_network_game
from ai import ai_move
import pygame
import sys

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
            main_menu_button, board_start_x, board_start_y, grid_size = draw_game_screen(screen, game, network_mode is not None)

            if game.is_over():
                winner = game.get_winner()
                action = show_winner_popup(screen, winner)
                if network:
                    network.close()
                return action

            if network_mode:
                move_data = network.check_network_data()
                if move_data:
                    if isinstance(move_data, list) and len(move_data) == 2:
                        row, col = move_data
                        if game.is_valid_move(row, col):
                            game.update_board(row, col)
                    else:
                        print(f"Received invalid move data format: {move_data}")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if main_menu_button.collidepoint(event.pos):
                        return "main_menu"
                    else:
                        x, y = event.pos
                        col = round((x - board_start_x) / grid_size)
                        row = round((y - board_start_y) / grid_size)
                        
                        if game.is_valid_move(row, col):
                            if network_mode:
                                if game.is_player_turn(game.player_color):
                                    if game.update_board(row, col):
                                        network.send_move(row, col)
                                else:
                                    print("现在不是你的回合！")
                            else:  # 本地模式（玩家对战或AI对战）
                                if game.update_board(row, col):
                                    if mode == "AI":
                                        draw_game_screen(screen, game, network_mode is not None)
                                        pygame.display.flip()
                                        pygame.time.wait(500)
                                        ai_move(game)

            pygame.display.flip()
            clock.tick(30)

    finally:
        if network:
            print("Closing network connection")
            network.close()
def game_loop():
    """游戏主循环"""
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

if __name__ == "__main__":
    game_loop()
