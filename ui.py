import pygame
import sys
from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE, MARGIN
from network import start_network_game, get_available_rooms, start_discovery_service, check_for_new_connection, start_server
from ai import ai_move

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (200, 200, 200)
BLUE = (0, 0, 255)




def draw_board(screen):
    """绘制棋盘"""
    screen.fill(WHITE)
    for i in range(BOARD_SIZE):
        # 画横线
        pygame.draw.line(screen, DARK_GRAY, 
                         (MARGIN, MARGIN + i * GRID_SIZE),
                         (SCREEN_SIZE - MARGIN, MARGIN + i * GRID_SIZE), 1)
        # 画竖线
        pygame.draw.line(screen, DARK_GRAY, 
                         (MARGIN + i * GRID_SIZE, MARGIN),
                         (MARGIN + i * GRID_SIZE, SCREEN_SIZE - MARGIN), 1)
    
    # 画边框
    pygame.draw.rect(screen, DARK_GRAY, 
                     (MARGIN, MARGIN, 
                      BOARD_SIZE * GRID_SIZE, BOARD_SIZE * GRID_SIZE), 2)

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

def input_port():
    """让用户输入端口号"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Enter Port Number")

    font = pygame.font.SysFont(None, 32)
    input_box = pygame.Rect(SCREEN_SIZE // 4, SCREEN_SIZE // 2, 250, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        try:
                            port = int(text)
                            if 1024 <= port <= 65535:
                                return port
                            else:
                                text = ''
                        except ValueError:
                            text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill(WHITE)
        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()

def waiting_room(is_host=True, network=None):
    print(f"Entering waiting room. Is host: {is_host}")
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Waiting Room")

    font = pygame.font.SysFont(None, 32)
    message = "Waiting for other player to join..." if is_host else "Waiting for host to start the game..."
    start_button = None

    if is_host:
        start_button = draw_button(screen, "Start Game", SCREEN_SIZE // 4, SCREEN_SIZE * 2 // 3, 250, 50)

    connection_established = network.connected if network else False

    while True:
        screen.fill(WHITE)
        text = font.render(message, True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2))
        screen.blit(text, text_rect)

        if is_host and connection_established:
            pygame.draw.rect(screen, LIGHT_GRAY, start_button)
            pygame.draw.rect(screen, DARK_GRAY, start_button, 2)
            start_text = font.render("Start Game", True, BLACK)
            start_text_rect = start_text.get_rect(center=start_button.center)
            screen.blit(start_text, start_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if network:
                    network.close()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and is_host and connection_established:
                if start_button.collidepoint(event.pos):
                    if network:
                        network.send({"type": "start_game"})
                    return network
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if network:
                    network.close()
                return "main_menu"

        if network:
            if is_host and not connection_established:
                client_socket = check_for_new_connection(network.server_socket)
                if client_socket:
                    network.client = client_socket  # 设置客户端 socket
                    connection_established = True
                    message = "Other player joined. Click 'Start Game' to begin."
                    print("Client connected.")
                    network.send({"type": "connection_established"})
            else:
                data = network.check_network_data()
                if data:
                    print(f"Received data in waiting room: {data}")
                    if isinstance(data, dict):
                        if data.get("type") == "connection_established":
                            print("Connection established")
                            connection_established = True
                            message = "Connected to host. Waiting for game to start..."
                        elif data.get("type") == "start_game":
                            print("Received start_game signal")
                            return network

        if not is_host and not connection_established:
            if not network.connected:
                connection_established = network.connect()
            if not connection_established:
                print("Failed to establish connection with the server.")
                return "main_menu"

        pygame.time.wait(100)

    return network

def show_available_rooms():
    """显示可用的房间列表"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Available Rooms")

    font = pygame.font.SysFont(None, 32)
    room_buttons = []

    available_rooms = get_available_rooms()

    while True:
        screen.fill(WHITE)
        text = font.render("Available Rooms", True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_SIZE // 2, 50))
        screen.blit(text, text_rect)

        for i, room in enumerate(available_rooms):
            button = draw_button(screen, f"Room {room['host']}:{room['port']}", SCREEN_SIZE // 4, 100 + i * 60, 250, 50)
            room_buttons.append((button, room))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button, room in room_buttons:
                    if button.collidepoint(event.pos):
                        return room['host'], room['port']

        # Add a small delay to reduce CPU usage
        pygame.time.wait(100)

def network_mode_selection():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Gomoku Network Mode Selection")

    screen.fill(WHITE)

    create_button = draw_button(screen, "Create Game", SCREEN_SIZE // 4, SCREEN_SIZE // 3, 250, 50)
    join_button = draw_button(screen, "Join Game", SCREEN_SIZE // 4, SCREEN_SIZE // 2, 250, 50)

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if create_button.collidepoint(event.pos):
                    port = input_port()
                    if port:
                        return "server", int(port)
                elif join_button.collidepoint(event.pos):
                    return "client", None  # Return None for port, we'll get it in show_available_rooms

        pygame.time.wait(100)

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



