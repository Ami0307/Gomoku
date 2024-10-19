# 定义一些基本参数
GRID_SIZE = 40
BOARD_SIZE = 15
MARGIN = GRID_SIZE  # 添加边距
SCREEN_SIZE = GRID_SIZE * (BOARD_SIZE + 1)  # 增加屏幕大小，为边距留出空间

class Game:
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = 'Black'
        self.winner = None
        self.player_color = None
        self.move_history = []

    def update_board(self, row, col):
        """更新棋盘状态"""
        if self.board[row][col] is None:
            self.board[row][col] = self.current_player
            self.move_history.append((row, col))
            if self.check_winner(row, col):
                self.winner = self.current_player
            self.switch_player()
            return True
        return False

    def switch_player(self):
        """切换当前玩家"""
        self.current_player = 'White' if self.current_player == 'Black' else 'Black'

    def check_winner(self, row, col):
        """检查是否有胜利者"""
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            for i in range(1, 5):
                r, c = row + i * dx, col + i * dy
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == self.current_player:
                    count += 1
                else:
                    break
            for i in range(1, 5):
                r, c = row - i * dx, col - i * dy
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == self.current_player:
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
