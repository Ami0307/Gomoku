from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE
from ui import main_menu, game_mode_selection, network_mode_selection, show_winner_popup, draw_board, draw_stones
from network import start_network_game
from ai import ai_move
import pygame


def start_game_ui():
    """启动游戏 UI，包括主菜单和模式选择"""
    game_mode = main_menu()
    if game_mode == "local":
        mode = game_mode_selection()
        return mode, None
    elif game_mode == "network":
        network_mode = network_mode_selection()
        return "Player", network_mode
    else:
        return None, None

def play_game(game, mode, network_mode=None):
    """实际的游戏循环"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Gomoku")

    CLICK_THRESHOLD = GRID_SIZE * 0.7

    network = None
    if network_mode:
        network = start_network_game(game, network_mode)

    while True:
        draw_board(screen)
        draw_stones(screen, game)

        if game.is_over():
            winner = game.get_winner()
            action = show_winner_popup(screen, winner)
            if network:
                network.close()
            return action

        pygame.display.flip()

        if network_mode and game.current_player != game.player_color:
            move = network.check_network_move()
            if move:
                game.update_board(move[0], move[1])
                continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if network:
                    network.close()
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                col = round((x - GRID_SIZE) / GRID_SIZE)
                row = round((y - GRID_SIZE) / GRID_SIZE)
                
                if 0 <= row < BOARD_SIZE - 1 and 0 <= col < BOARD_SIZE - 1:
                    if game.is_valid_move(row, col):
                        if game.update_board(row, col):
                            if network_mode:
                                network.send_move(row, col)
                            elif mode == "AI" and not game.is_over():
                                ai_move(game)

def game_loop():
    """游戏主循环"""
    while True:
        game = Game()
        mode, network_mode = start_game_ui()
        if mode is None:
            break
        
        while True:
            action = play_game(game, mode, network_mode)
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