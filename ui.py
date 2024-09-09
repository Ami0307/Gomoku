import pygame
import sys
from common import Game
from network import start_network_game
from ai import ai_move

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (200, 200, 200)
BLUE = (0, 0, 255)

# 定义一些基本参数
GRID_SIZE = 40
BOARD_SIZE = 15
SCREEN_SIZE = GRID_SIZE * BOARD_SIZE

def draw_board(screen):
    """绘制棋盘"""
    screen.fill(WHITE)
    for i in range(BOARD_SIZE):
        # 画横线
        pygame.draw.line(screen, DARK_GRAY, (GRID_SIZE, GRID_SIZE * (i + 1)),
                         (SCREEN_SIZE - GRID_SIZE, GRID_SIZE * (i + 1)), 1)
        # 画竖线
        pygame.draw.line(screen, DARK_GRAY, (GRID_SIZE * (i + 1), GRID_SIZE),
                         (GRID_SIZE * (i + 1), SCREEN_SIZE - GRID_SIZE), 1)
    
    # 画边框
    pygame.draw.rect(screen, DARK_GRAY, (GRID_SIZE, GRID_SIZE, 
                     SCREEN_SIZE - 2 * GRID_SIZE, SCREEN_SIZE - 2 * GRID_SIZE), 2)

def draw_stones(screen, game):
    """绘制棋子"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game.board[row][col] == 'Black':
                pygame.draw.circle(screen, BLACK, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1)),
                                   GRID_SIZE // 2 - 2)
            elif game.board[row][col] == 'White':
                pygame.draw.circle(screen, WHITE, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1)),
                                   GRID_SIZE // 2 - 2)
                pygame.draw.circle(screen, BLACK, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1)),
                                   GRID_SIZE // 2 - 2, 1)

def draw_button(screen, text, x, y, width, height):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
    pygame.draw.rect(screen, DARK_GRAY, button_rect, 2)
    font = pygame.font.SysFont(None, 32)
    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect

def main_menu():
    """显示主菜单"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Gomoku Main Menu")

    screen.fill(WHITE)  # 设置白色背景

    local_button = draw_button(screen, "Local Game", SCREEN_SIZE // 4, SCREEN_SIZE // 3, 250, 50)
    network_button = draw_button(screen, "Network Game", SCREEN_SIZE // 4, SCREEN_SIZE // 2, 250, 50)
    quit_button = draw_button(screen, "Quit", SCREEN_SIZE // 4, SCREEN_SIZE * 2 // 3, 250, 50)

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if local_button.collidepoint(event.pos):
                    return "local"
                elif network_button.collidepoint(event.pos):
                    return "network"
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

def game_mode_selection():
    """选择游戏模式（AI 或玩家对战）"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Gomoku Mode Selection")

    screen.fill(WHITE)  # 设置白色背景

    ai_button = draw_button(screen, "Play against AI", SCREEN_SIZE // 4, SCREEN_SIZE // 3, 250, 50)
    player_button = draw_button(screen, "Play against Player", SCREEN_SIZE // 4, SCREEN_SIZE // 2, 250, 50)

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ai_button.collidepoint(event.pos):
                    return "AI"
                elif player_button.collidepoint(event.pos):
                    return "Player"

def network_mode_selection():
    """选择网络模式（服务器或客户端）"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Gomoku Network Mode Selection")

    screen.fill(WHITE)  # 设置白色背景

    server_button = draw_button(screen, "Create Server", SCREEN_SIZE // 4, SCREEN_SIZE // 3, 250, 50)
    client_button = draw_button(screen, "Join Game", SCREEN_SIZE // 4, SCREEN_SIZE // 2, 250, 50)

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if server_button.collidepoint(event.pos):
                    return "server"
                elif client_button.collidepoint(event.pos):
                    return "client"

def show_winner_popup(screen, winner):
    """显示获胜者弹窗，并提供再来一局、返回主菜单和退出选项"""
    popup_width, popup_height = 300, 250
    popup_x = (SCREEN_SIZE - popup_width) // 2
    popup_y = (SCREEN_SIZE - popup_height) // 2

    popup = pygame.Surface((popup_width, popup_height))
    popup.fill(WHITE)
    pygame.draw.rect(popup, DARK_GRAY, (0, 0, popup_width, popup_height), 2)

    font = pygame.font.SysFont(None, 36)
    if winner == "Draw":
        message = "Game Over! It's a Draw!"
    else:
        message = f"Game Over! {winner} Wins!"
    text = font.render(message, True, BLACK)
    text_rect = text.get_rect(center=(popup_width // 2, popup_height // 5))
    popup.blit(text, text_rect)

    button_font = pygame.font.SysFont(None, 32)
    play_again_text = button_font.render("Play Again", True, BLACK)
    main_menu_text = button_font.render("Main Menu", True, BLACK)
    quit_text = button_font.render("Quit", True, BLACK)

    play_again_rect = pygame.Rect(50, popup_height * 2 // 5, 200, 40)
    main_menu_rect = pygame.Rect(50, popup_height * 3 // 5, 200, 40)
    quit_rect = pygame.Rect(50, popup_height * 4 // 5, 200, 40)

    pygame.draw.rect(popup, LIGHT_GRAY, play_again_rect)
    pygame.draw.rect(popup, LIGHT_GRAY, main_menu_rect)
    pygame.draw.rect(popup, LIGHT_GRAY, quit_rect)

    popup.blit(play_again_text, (play_again_rect.centerx - play_again_text.get_width() // 2, play_again_rect.centery - play_again_text.get_height() // 2))
    popup.blit(main_menu_text, (main_menu_rect.centerx - main_menu_text.get_width() // 2, main_menu_rect.centery - main_menu_text.get_height() // 2))
    popup.blit(quit_text, (quit_rect.centerx - quit_text.get_width() // 2, quit_rect.centery - quit_text.get_height() // 2))

    screen.blit(popup, (popup_x, popup_y))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if play_again_rect.collidepoint((mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)):
                    return "play_again"
                elif main_menu_rect.collidepoint((mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)):
                    return "main_menu"
                elif quit_rect.collidepoint((mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)):
                    return "quit"



