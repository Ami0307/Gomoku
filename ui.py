import pygame
import sys
from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE, MARGIN, toggle_fullscreen, get_screen, is_fullscreen, get_screen_size, bgm_enabled, sound_enabled, is_fullscreen, toggle_bgm, toggle_sound, toggle_fullscreen, get_bgm_enabled
from network import start_network_game, get_available_rooms, start_discovery_service, check_for_new_connection, start_server
from ai import ai_move
import pygame.mixer

pygame.init()
pygame.font.init()
# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BOARD_COLOR = (250, 214, 165)  # 添加这行，定义棋盘背景色
# 字体设置
FONT_PATH = "fonts/SimHei.ttf"
FONT_SIZE = 32

def load_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except IOError:
        print(f"无法加载字体文件: {FONT_PATH}，使用系统默认字体")
        return pygame.font.SysFont(None, size)

# 初始化字体
GAME_FONT = load_font(FONT_SIZE)



def draw_stones(screen, game):
    """绘制棋子"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game.board[row][col] == 'Black':
                pygame.draw.circle(screen, BLACK, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1) + 40),
                                   GRID_SIZE // 2 - 2)
            elif game.board[row][col] == 'White':
                pygame.draw.circle(screen, WHITE, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1) + 40),
                                   GRID_SIZE // 2 - 2)
                pygame.draw.circle(screen, BLACK, (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1) + 40),
                                   GRID_SIZE // 2 - 2, 1)
# 高亮显示最后两步棋
    last_two_moves = game.move_history[-2:]
    for i, (row, col) in enumerate(reversed(last_two_moves)):
        center = (GRID_SIZE * (col + 1), GRID_SIZE * (row + 1) + 40)
        color = RED if i == 0 else GREEN  # 最后一步为红色，倒数第二步为绿色
        rect_size = GRID_SIZE - 4  # 方块大小稍小于格子大小
        rect = pygame.Rect(center[0] - rect_size // 2, center[1] - rect_size // 2, rect_size, rect_size)
        pygame.draw.rect(screen, color, rect, 3)  # 绘制方块边框，宽度为3
def draw_button(screen, text, x, y, width, height):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, LIGHT_GRAY, button_rect)
    pygame.draw.rect(screen, DARK_GRAY, button_rect, 2)
    text_surface = GAME_FONT.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect


def main_menu():
    """显示主菜单"""
    screen = get_screen()
    pygame.display.set_caption("五子棋主菜单")

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)

        button_width = 250
        button_height = 50
        button_margin = 20
        total_height = 4 * button_height + 3 * button_margin
        start_y = (screen_height - total_height) // 2

        local_button = draw_button(screen, "本地游戏", (screen_width - button_width) // 2, start_y, button_width, button_height)
        network_button = draw_button(screen, "网络游戏", (screen_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height)
        settings_button = draw_button(screen, "设置", (screen_width - button_width) // 2, start_y + 2 * (button_height + button_margin), button_width, button_height)
        quit_button = draw_button(screen, "退出", (screen_width - button_width) // 2, start_y + 3 * (button_height + button_margin), button_width, button_height)

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
                elif settings_button.collidepoint(event.pos):
                    settings_menu()
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.time.wait(100)

def game_mode_selection():
    """选择游戏模式（AI 或玩家对战）"""
    screen = get_screen()
    pygame.display.set_caption("五子棋模式选择")

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)

        title_font = pygame.font.Font(FONT_PATH, 40)
        title_surface = title_font.render("选择游戏模式", True, BLACK)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_surface, title_rect)

        button_width, button_height = 250, 50
        button_margin = 20
        total_height = 2 * button_height + button_margin
        start_y = (screen_height - total_height) // 2

        ai_button = draw_button(screen, "对战AI", (screen_width - button_width) // 2, start_y, button_width, button_height)
        player_button = draw_button(screen, "玩家对战", (screen_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height)

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

        pygame.time.wait(100)

def input_port():
    """让用户输入端口号"""
    screen = get_screen()
    pygame.display.set_caption("输入端口号")

    font = load_font(32)
    small_font = load_font(24)
    screen_width, screen_height = get_screen_size()

    input_box = pygame.Rect(screen_width // 4, screen_height // 2 - 20, screen_width // 2, 40)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_active
    active = True
    text = ''
    error_message = ''

    title_surface = font.render("请输入端口号 (1024-65535)", True, BLACK)
    title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 3))

    confirm_button = pygame.Rect(screen_width // 2 - 60, screen_height * 2 // 3, 120, 40)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = True
                elif confirm_button.collidepoint(event.pos):
                    try:
                        port = int(text)
                        if 1024 <= port <= 65535:
                            return port
                        else:
                            error_message = "端口号必须在1024到65535之间。"
                    except ValueError:
                        error_message = "请输入有效的端口号。"
                else:
                    active = False
                color = color_active if active else color_inactive
            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        try:
                            port = int(text)
                            if 1024 <= port <= 65535:
                                return port
                            else:
                                error_message = "端口号必须在1024到65535之间。"
                        except ValueError:
                            error_message = "请输入有效的端口号。"
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.unicode.isdigit():
                        text += event.unicode

        screen.fill(BOARD_COLOR)

        # 绘制标题
        screen.blit(title_surface, title_rect)

        # 绘制输入框
        txt_surface = font.render(text, True, BLACK)
        width = max(input_box.w, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        # 绘制确认按钮
        pygame.draw.rect(screen, LIGHT_GRAY, confirm_button)
        pygame.draw.rect(screen, DARK_GRAY, confirm_button, 2)
        confirm_text = small_font.render("确认", True, BLACK)
        confirm_text_rect = confirm_text.get_rect(center=confirm_button.center)
        screen.blit(confirm_text, confirm_text_rect)

        # 显示错误消息
        if error_message:
            error_surface = small_font.render(error_message, True, RED)
            error_rect = error_surface.get_rect(center=(screen_width // 2, screen_height * 3 // 4))
            screen.blit(error_surface, error_rect)

        pygame.display.flip()
        pygame.time.wait(100)

def waiting_room(is_host=True, network=None):
    print(f"进入等待房间。是否为主机: {is_host}")
    pygame.init()
    screen = get_screen()
    pygame.display.set_caption("等待房间")

    message = "等待其他玩家加入..." if is_host else "等待主机开始游戏..."
    start_button = None

    if is_host:
        start_button = draw_button(screen, "开始游戏", SCREEN_SIZE // 4, SCREEN_SIZE * 2 // 3, 250, 50)

    connection_established = network.connected if network else False

    while True:
        screen.fill(BOARD_COLOR)
        text = GAME_FONT.render(message, True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2))
        screen.blit(text, text_rect)

        if is_host and connection_established:
            pygame.draw.rect(screen, LIGHT_GRAY, start_button)
            pygame.draw.rect(screen, DARK_GRAY, start_button, 2)
            start_text = GAME_FONT.render("开始游戏", True, BLACK)
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
                    message = "其他玩家加入。点击 '开始游戏' 开始游戏。"
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
                            message = "已连接到机。等待游戏开始..."
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
    screen = get_screen()
    pygame.display.set_caption("可用房间")

    available_rooms = get_available_rooms()

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)

        # 标题
        title_font = pygame.font.Font(FONT_PATH, 40)
        title_surface = title_font.render("可用房间", True, BLACK)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 6))
        screen.blit(title_surface, title_rect)

        # 调整按钮尺寸
        button_width = 500  # 增加按钮宽度
        button_height = 60  # 增加按钮高度
        button_margin = 20
        total_height = (len(available_rooms) + 1) * (button_height + button_margin)
        start_y = (screen_height - total_height) // 2

        # 房间列表
        room_buttons = []
        for i, room in enumerate(available_rooms):
            # 创建按钮
            button = draw_button(screen, "", 
                               (screen_width - button_width) // 2, 
                               start_y + i * (button_height + button_margin), 
                               button_width, button_height)
            
            # 房间编号（左侧）
            room_font = pygame.font.Font(FONT_PATH, 20)
            room_text = f"房间 {i+1}"
            room_surface = room_font.render(room_text, True, BLACK)
            room_rect = room_surface.get_rect(
                midleft=(button.left + 20, button.centery)
            )
            screen.blit(room_surface, room_rect)
            
            # 地址信息（右侧）
            addr_font = pygame.font.Font(FONT_PATH, 18)
            addr_text = f"{room['host']}:{room['port']}"
            addr_surface = addr_font.render(addr_text, True, BLACK)
            addr_rect = addr_surface.get_rect(
                midright=(button.right - 20, button.centery)
            )
            screen.blit(addr_surface, addr_rect)
            
            room_buttons.append((button, room))

        # 返回按钮
        back_button = draw_button(screen, "返回", 
                                (screen_width - button_width) // 2, 
                                start_y + len(available_rooms) * (button_height + button_margin), 
                                button_width, button_height)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button, room in room_buttons:
                    if button.collidepoint(event.pos):
                        return room['host'], room['port']
                if back_button.collidepoint(event.pos):
                    return None, None

        pygame.time.wait(100)

def network_mode_selection():
    screen = get_screen()
    pygame.display.set_caption("五子棋网络模式选择")

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)

        title_font = pygame.font.Font(FONT_PATH, 40)
        title_surface = title_font.render("选择网络模式", True, BLACK)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_surface, title_rect)

        button_width, button_height = 250, 50
        button_margin = 20
        total_height = 3 * button_height + 2 * button_margin
        start_y = (screen_height - total_height) // 2

        host_button = draw_button(screen, "创建房间", (screen_width - button_width) // 2, start_y, button_width, button_height)
        join_button = draw_button(screen, "加房间", (screen_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height)
        back_button = draw_button(screen, "返回", (screen_width - button_width) // 2, start_y + 2 * (button_height + button_margin), button_width, button_height)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if host_button.collidepoint(event.pos):
                    port = input_port()
                    return "server", int(port)
                elif join_button.collidepoint(event.pos):
                    return "client", None
                elif back_button.collidepoint(event.pos):
                    return "back", None

        pygame.time.wait(100)

def show_winner_popup(screen, winner):
    """显示获胜者弹窗，提供再来一局、返回主菜单和退出选项"""
    screen_width, screen_height = get_screen_size()
    popup_width, popup_height = min(500, screen_width - 40), min(400, screen_height - 40)
    popup_x = (screen_width - popup_width) // 2
    popup_y = (screen_height - popup_height) // 2

    popup = pygame.Surface((popup_width, popup_height))
    popup.fill(WHITE)
    pygame.draw.rect(popup, DARK_GRAY, (0, 0, popup_width, popup_height), 2)

    # 标
    title_font = pygame.font.Font(FONT_PATH, 48)
    title = title_font.render("游戏结束", True, BLACK)
    title_rect = title.get_rect(center=(popup_width // 2, popup_height // 7))  # 将标题向上移动
    popup.blit(title, title_rect)

    # 结果消息
    message_font = pygame.font.Font(FONT_PATH, 36)
    if winner == "Draw":
        message = "平局！"
    else:
        message = f"{winner}获胜！"
    message_text = message_font.render(message, True, BLACK)
    message_rect = message_text.get_rect(center=(popup_width // 2, popup_height // 3))  # 将消息向上移动
    popup.blit(message_text, message_rect)

    button_width, button_height = 200, 50
    button_margin = 25  # 稍微减小按钮间距
    total_buttons_height = 3 * button_height + 2 * button_margin
    start_y = popup_height * 2 // 5  # 将按钮整体向上移动

    play_again_rect = pygame.Rect((popup_width - button_width) // 2, start_y, button_width, button_height)
    main_menu_rect = pygame.Rect((popup_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height)
    quit_rect = pygame.Rect((popup_width - button_width) // 2, start_y + 2 * (button_height + button_margin), button_width, button_height)

    button_color = LIGHT_GRAY
    button_hover_color = (220, 220, 220)
    text_color = BLACK

    buttons = [
        (play_again_rect, "再来一局"),
        (main_menu_rect, "主菜单"),
        (quit_rect, "退出")
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        relative_pos = (mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)

        for rect, text in buttons:
            if rect.collidepoint(relative_pos):
                pygame.draw.rect(popup, button_hover_color, rect)
            else:
                pygame.draw.rect(popup, button_color, rect)
            pygame.draw.rect(popup, DARK_GRAY, rect, 2)
            button_text = GAME_FONT.render(text, True, text_color)
            text_rect = button_text.get_rect(center=rect.center)
            popup.blit(button_text, text_rect)

        screen.blit(popup, (popup_x, popup_y))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_rect.collidepoint(relative_pos):
                    return "play_again"
                elif main_menu_rect.collidepoint(relative_pos):
                    return "main_menu"
                elif quit_rect.collidepoint(relative_pos):
                    return "quit"

        pygame.time.wait(100)

def draw_game_screen(screen, game, network_mode=False):
    screen_width, screen_height = get_screen_size()
    screen.fill(BOARD_COLOR)
    
    # 菜单栏高度和背景
    menu_height = 40  # 统一使用单行高度
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, screen_width, menu_height))
    pygame.draw.line(screen, BLACK, (0, menu_height), (screen_width, menu_height), 2)

    # 所有元素垂直居中
    vertical_center = menu_height // 2
    margin = 10
    current_x = margin

    # 主菜单按钮（左侧）
    button_height = 30
    button_width = 80
    main_menu_button = draw_button(screen, "主菜单", current_x, (menu_height - button_height) // 2, button_width, button_height)
    current_x = main_menu_button.right + margin

    # 悔棋按钮
    undo_button = draw_button(screen, "悔棋", current_x, (menu_height - button_height) // 2, button_width, button_height)
    current_x = undo_button.right + margin

    # 悔棋次数
    info_font = pygame.font.Font(FONT_PATH, 16)
    undo_text = f"剩余次数:{3 - game.black_undo_count if game.current_player == 'Black' else 3 - game.white_undo_count}"
    undo_surface = info_font.render(undo_text, True, WHITE)
    undo_rect = undo_surface.get_rect(centery=vertical_center, left=current_x)
    screen.blit(undo_surface, undo_rect)
    current_x = undo_rect.right + margin * 2

    # 当前回合信息
    turn_text = f"当前回合:{'黑棋' if game.current_player == 'Black' else '白棋'}"
    turn_surface = info_font.render(turn_text, True, WHITE)
    turn_rect = turn_surface.get_rect(centery=vertical_center, left=current_x)
    screen.blit(turn_surface, turn_rect)
    current_x = turn_rect.right + margin * 2

    # 网络模式下显示玩家颜色
    if network_mode:
        color_text = f"你的颜色:{'黑棋' if game.player_color == 'Black' else '白棋'}"
        color_surface = info_font.render(color_text, True, WHITE)
        color_rect = color_surface.get_rect(centery=vertical_center, left=current_x)
        screen.blit(color_surface, color_rect)

    # BGM 复选框（右侧）
    checkbox_size = 16
    checkbox_margin = 5
    bgm_checkbox_rect = pygame.Rect(
        screen_width - checkbox_size - checkbox_margin - 40, 
        (menu_height - checkbox_size) // 2,
        checkbox_size, 
        checkbox_size
    )
    
    # 绘制BGM控件
    pygame.draw.rect(screen, WHITE, bgm_checkbox_rect)
    pygame.draw.rect(screen, BLACK, bgm_checkbox_rect, 2)
    if get_bgm_enabled():
        pygame.draw.line(screen, BLACK, 
                        (bgm_checkbox_rect.left + 3, bgm_checkbox_rect.centery),
                        (bgm_checkbox_rect.centerx, bgm_checkbox_rect.bottom - 3), 2)
        pygame.draw.line(screen, BLACK,
                        (bgm_checkbox_rect.centerx, bgm_checkbox_rect.bottom - 3),
                        (bgm_checkbox_rect.right - 3, bgm_checkbox_rect.top + 3), 2)

    bgm_label = info_font.render("BGM", True, WHITE)
    bgm_label_rect = bgm_label.get_rect(midright=(bgm_checkbox_rect.left - 5, bgm_checkbox_rect.centery))
    screen.blit(bgm_label, bgm_label_rect)

    # 计算棋盘大小和位置
    board_size = min(screen_width, screen_height - menu_height) - 2 * MARGIN
    grid_size = board_size // (BOARD_SIZE - 1)
    board_size = grid_size * (BOARD_SIZE - 1)  # 重新计算board_size，确保它是grid_size的整数倍
    board_start_x = (screen_width - board_size) // 2
    board_start_y = menu_height + (screen_height - menu_height - board_size) // 2

    # 绘制棋盘
    for i in range(BOARD_SIZE):
        pygame.draw.line(screen, BLACK,
                         (board_start_x, board_start_y + i * grid_size),
                         (board_start_x + board_size, board_start_y + i * grid_size), 1)
        pygame.draw.line(screen, BLACK,
                         (board_start_x + i * grid_size, board_start_y),
                         (board_start_x + i * grid_size, board_start_y + board_size), 1)
    
    # 绘制棋盘边框
    pygame.draw.rect(screen, BLACK,
                     (board_start_x, board_start_y, board_size, board_size), 2)

    # 绘制棋子
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            center_x = board_start_x + col * grid_size
            center_y = board_start_y + row * grid_size
            if game.board[row][col] == 'Black':
                pygame.draw.circle(screen, BLACK, (center_x, center_y), grid_size // 2 - 2)
            elif game.board[row][col] == 'White':
                pygame.draw.circle(screen, WHITE, (center_x, center_y), grid_size // 2 - 2)
                pygame.draw.circle(screen, BLACK, (center_x, center_y), grid_size // 2 - 2, 1)

    # 高亮显示最后两步棋
    last_two_moves = game.move_history[-2:]
    for i, (row, col) in enumerate(reversed(last_two_moves)):
        center_x = board_start_x + col * grid_size
        center_y = board_start_y + row * grid_size
        color = RED if i == 0 else GREEN
        rect_size = grid_size - 4
        rect = pygame.Rect(center_x - rect_size // 2, center_y - rect_size // 2, rect_size, rect_size)
        pygame.draw.rect(screen, color, rect, 3)

    # 如果不能悔棋，将悔棋按钮设置为灰色
    if not game.can_undo():
        pygame.draw.rect(screen, DARK_GRAY, undo_button)  # 使用深灰色表示禁用状态
    else:
        pygame.draw.rect(screen, LIGHT_GRAY, undo_button)
    pygame.draw.rect(screen, BLACK, undo_button, 2)
    undo_text = GAME_FONT.render("悔棋", True, BLACK if game.can_undo() else DARK_GRAY)
    undo_text_rect = undo_text.get_rect(center=undo_button.center)
    screen.blit(undo_text, undo_text_rect)

    pygame.display.flip()

    return main_menu_button, undo_button, board_start_x, board_start_y, grid_size, bgm_checkbox_rect

def choose_first_player():
    screen = get_screen()
    pygame.display.set_caption("选择先手")

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)

        title_font = pygame.font.Font(FONT_PATH, 40)
        title_surface = title_font.render("谁先手？", True, BLACK)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_surface, title_rect)

        button_width, button_height = 250, 50
        button_margin = 20
        total_height = 2 * button_height + button_margin
        start_y = (screen_height - total_height) // 2

        player_button = draw_button(screen, "玩家", (screen_width - button_width) // 2, start_y, button_width, button_height)
        ai_button = draw_button(screen, "AI", (screen_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if player_button.collidepoint(event.pos):
                    return "Player"
                elif ai_button.collidepoint(event.pos):
                    return "AI"

        pygame.time.wait(100)

def settings_menu():
    global bgm_enabled, sound_enabled, is_fullscreen
    screen = get_screen()
    pygame.display.set_caption("设置")

    checkbox_size = 30
    checkbox_color = WHITE
    check_color = BLACK

    while True:
        screen = get_screen()
        screen_width, screen_height = get_screen_size()
        screen.fill(BOARD_COLOR)
        
        title_font = pygame.font.Font(FONT_PATH, 40)
        title_surface = title_font.render("设置", True, BLACK)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 6))
        screen.blit(title_surface, title_rect)

        button_width, button_height = 250, 50
        checkbox_margin = 20
        total_height = 3 * (checkbox_size + checkbox_margin) + button_height
        start_y = (screen_height - total_height) // 2

        # 全屏模式复选框
        fullscreen_checkbox_rect = pygame.Rect((screen_width - checkbox_size) // 2 - 100, start_y, checkbox_size, checkbox_size)
        pygame.draw.rect(screen, checkbox_color, fullscreen_checkbox_rect)
        pygame.draw.rect(screen, BLACK, fullscreen_checkbox_rect, 2)
        if is_fullscreen:
            pygame.draw.line(screen, check_color, (fullscreen_checkbox_rect.left + 5, fullscreen_checkbox_rect.centery), (fullscreen_checkbox_rect.centerx, fullscreen_checkbox_rect.bottom - 5), 3)
            pygame.draw.line(screen, check_color, (fullscreen_checkbox_rect.centerx, fullscreen_checkbox_rect.bottom - 5), (fullscreen_checkbox_rect.right - 5, fullscreen_checkbox_rect.top + 5), 3)

        fullscreen_label_font = pygame.font.Font(FONT_PATH, 24)
        fullscreen_label_surface = fullscreen_label_font.render("全屏模式", True, BLACK)
        fullscreen_label_rect = fullscreen_label_surface.get_rect(midleft=(fullscreen_checkbox_rect.right + 10, fullscreen_checkbox_rect.centery))
        screen.blit(fullscreen_label_surface, fullscreen_label_rect)

        # 音效复选框
        sound_checkbox_rect = pygame.Rect((screen_width - checkbox_size) // 2 - 100, start_y + checkbox_size + checkbox_margin, checkbox_size, checkbox_size)
        pygame.draw.rect(screen, checkbox_color, sound_checkbox_rect)
        pygame.draw.rect(screen, BLACK, sound_checkbox_rect, 2)
        if sound_enabled:
            pygame.draw.line(screen, check_color, (sound_checkbox_rect.left + 5, sound_checkbox_rect.centery), (sound_checkbox_rect.centerx, sound_checkbox_rect.bottom - 5), 3)
            pygame.draw.line(screen, check_color, (sound_checkbox_rect.centerx, sound_checkbox_rect.bottom - 5), (sound_checkbox_rect.right - 5, sound_checkbox_rect.top + 5), 3)

        sound_label_font = pygame.font.Font(FONT_PATH, 24)
        sound_label_surface = sound_label_font.render("音效", True, BLACK)
        sound_label_rect = sound_label_surface.get_rect(midleft=(sound_checkbox_rect.right + 10, sound_checkbox_rect.centery))
        screen.blit(sound_label_surface, sound_label_rect)

        # BGM 复选框
        bgm_checkbox_rect = pygame.Rect((screen_width - checkbox_size) // 2 - 100, start_y + 2 * (checkbox_size + checkbox_margin), checkbox_size, checkbox_size)
        pygame.draw.rect(screen, checkbox_color, bgm_checkbox_rect)
        pygame.draw.rect(screen, BLACK, bgm_checkbox_rect, 2)
        if get_bgm_enabled():
            pygame.draw.line(screen, check_color, (bgm_checkbox_rect.left + 5, bgm_checkbox_rect.centery), (bgm_checkbox_rect.centerx, bgm_checkbox_rect.bottom - 5), 3)
            pygame.draw.line(screen, check_color, (bgm_checkbox_rect.centerx, bgm_checkbox_rect.bottom - 5), (bgm_checkbox_rect.right - 5, bgm_checkbox_rect.top + 5), 3)

        bgm_label_font = pygame.font.Font(FONT_PATH, 24)
        bgm_label_surface = bgm_label_font.render("背景音乐", True, BLACK)
        bgm_label_rect = bgm_label_surface.get_rect(midleft=(bgm_checkbox_rect.right + 10, bgm_checkbox_rect.centery))
        screen.blit(bgm_label_surface, bgm_label_rect)

        back_button = draw_button(screen, "返回", (screen_width - button_width) // 2, start_y + 3 * (checkbox_size + checkbox_margin), button_width, button_height)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if fullscreen_checkbox_rect.collidepoint(event.pos):
                    is_fullscreen = toggle_fullscreen()
                    screen = get_screen()  # 立即更新屏幕对象
                elif sound_checkbox_rect.collidepoint(event.pos):
                    sound_enabled = toggle_sound()
                elif bgm_checkbox_rect.collidepoint(event.pos):
                    bgm_enabled = toggle_bgm()
                elif back_button.collidepoint(event.pos):
                    return

        # 在每次循环中重新绘制复选框
        draw_checkbox(screen, fullscreen_checkbox_rect, is_fullscreen)
        draw_checkbox(screen, sound_checkbox_rect, sound_enabled)
        draw_checkbox(screen, bgm_checkbox_rect, bgm_enabled)

        pygame.display.flip()

def draw_checkbox(screen, rect, is_checked):
    pygame.draw.rect(screen, WHITE, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    if is_checked:
        pygame.draw.line(screen, BLACK, (rect.left + 5, rect.centery), 
                         (rect.centerx, rect.bottom - 5), 3)
        pygame.draw.line(screen, BLACK, (rect.centerx, rect.bottom - 5), 
                         (rect.right - 5, rect.top + 5), 3)







