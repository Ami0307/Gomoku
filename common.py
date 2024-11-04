# 定义一些基本参数
GRID_SIZE = 40
BOARD_SIZE = 15
MARGIN = GRID_SIZE  # 添加边距
SCREEN_SIZE = GRID_SIZE * (BOARD_SIZE + 1)  # 增加屏幕大小，为边距留出空间

# 在文件顶部添加全局变量
global bgm_enabled, sound_enabled, is_fullscreen, screen
bgm_enabled = True
sound_enabled = True
is_fullscreen = False
screen = None

import pygame
import pygame.mixer
pygame.init()
def get_move_sound():
    return sound_enabled
def get_bgm_enabled():
    return bgm_enabled
def load_sound():
    global move_sound, bgm
    move_sound = pygame.mixer.Sound("sounds/move.wav")
    bgm = pygame.mixer.music.load("sounds/music.wav")  # 请确保你有一个背景音乐文件

def play_bgm():
    if bgm_enabled:
        pygame.mixer.music.play(-1)  # -1 表示循环播放

def stop_bgm():
    pygame.mixer.music.stop()

load_sound()
play_bgm()
def toggle_bgm():
    global bgm_enabled
    bgm_enabled = not bgm_enabled
    if bgm_enabled:
        # 启动背景音乐
        play_bgm()
    else:
        # 停止背景音乐
        stop_bgm()
    return bgm_enabled

def toggle_sound():
    global sound_enabled
    sound_enabled = not sound_enabled
    return sound_enabled

def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.flip()  # 确保显示更新
    return is_fullscreen

def get_screen():
    global screen
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    return screen

def get_screen_size():
    screen = get_screen()
    return screen.get_width(), screen.get_height()

class Game:
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = 'Black'
        self.winner = None
        self.player_color = None
        self.move_history = []
        self.black_undo_count = 0  # 黑方已用悔棋次数
        self.white_undo_count = 0  # 白方已用悔棋次数
        self.last_move_after_undo = False  # 标记是否在上次悔棋后走了新的一步

    def update_board(self, row, col):
        """更新棋盘状态"""
        if self.board[row][col] is None:
            self.board[row][col] = self.current_player
            self.move_history.append((row, col))
            self.last_move_after_undo = True  # 有新的移动，可以再次悔棋
            if self.check_winner():
                self.winner = self.current_player
            self.switch_player()
            return True
        return False

    def switch_player(self):
        """切换当前玩家"""
        self.current_player = 'White' if self.current_player == 'Black' else 'Black'

    def check_winner(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] is not None:
                    if self.check_winner_at(row, col):
                        return self.board[row][col]
        
        # 检查是否平局
        if all(all(row) for row in self.board):
            return "Draw"
        
        return None

    def check_winner_at(self, row, col):
        player = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            count = 1
            for i in range(1, 5):
                new_row, new_col = row + i*dx, col + i*dy
                if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE and self.board[new_row][new_col] == player:
                    count += 1
                else:
                    break
            
            for i in range(1, 5):
                new_row, new_col = row - i*dx, col - i*dy
                if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE and self.board[new_row][new_col] == player:
                    count += 1
                else:
                    break
            
            if count >= 5:
                return True
        
        return False

    def is_over(self):
        """判断游戏是否结束"""
        if self.winner is not None:
            return True
        
        # 查是否还有空位
        for row in self.board:
            if None in row:
                return False
        
        # 如果没有空位且没有胜者，则为平局
        return True

    def get_winner(self):
        """返回获胜玩家"""
        if self.winner:
            return self.winner
        elif self.is_over():
            return "Draw"
        else:
            return None

    def handle_network_data(self, data):
        if data["type"] == "move":
            row, col = data["row"], data["col"]
            self.update_board(row, col)
            return {"status": "success", "board": self.board}
        return {"status": "error", "message": "Invalid data"}

    def is_valid_move(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] is None

    def handle_network_move(self, move_data):
        if isinstance(move_data, list) and len(move_data) == 2:
            row, col = move_data
            if self.is_valid_move(row, col):
                return self.update_board(row, col)
        return False

    def is_player_turn(self, player_color):
        return self.current_player == player_color

    def can_undo(self):
        """检查当前玩家是否可以悔棋"""
        if not self.move_history:  # 没有历史记录
            return False
            
        if not self.last_move_after_undo:  # 上次悔棋后没有新的移动
            return False
            
        # 检查剩余次数
        if self.current_player == 'Black':
            return self.black_undo_count < 3
        else:
            return self.white_undo_count < 3

    def undo_move(self, steps=1):
        """撤回指定步数的移动"""
        if not self.can_undo():
            return False
            
        if len(self.move_history) < steps:
            return False
            
        # 更新悔棋次数
        if self.current_player == 'Black':
            self.black_undo_count += 1
        else:
            self.white_undo_count += 1
            
        # 执行悔棋
        for _ in range(steps):
            if self.move_history:
                row, col = self.move_history.pop()
                self.board[row][col] = None
                self.switch_player()  # 切换回上一个玩家
        
        self.last_move_after_undo = False  # 标记刚进行过悔棋
        return True
