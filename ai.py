import random
from common import Game, SCREEN_SIZE, GRID_SIZE, BOARD_SIZE, MARGIN

def ai_move(game):
    print("AI 正在思考...")
    best_score = float('-inf')
    best_moves = []
    
    # 检查是否有立即获胜的机会
    winning_move = find_winning_move(game, game.current_player)
    if winning_move:
        return game.update_board(*winning_move)
    
    # 检查是否需要阻止对手获胜
    opponent = 'White' if game.current_player == 'Black' else 'Black'
    blocking_move = find_winning_move(game, opponent)
    if blocking_move:
        return game.update_board(*blocking_move)
    
    # 如果没有紧急情况，评估所有可能的移动
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if game.is_valid_move(i, j):
                score = evaluate_move(game, i, j)
                if score > best_score:
                    best_score = score
                    best_moves = [(i, j)]
                elif score == best_score:
                    best_moves.append((i, j))
    
    if best_moves:
        row, col = random.choice(best_moves)
        return game.update_board(row, col)
    else:
        print("AI 没有可用的移动")

def find_winning_move(game, player):
    for i in range(15):
        for j in range(15):
            if game.board[i][j] is None:
                game.board[i][j] = player
                if game.check_winner(i, j):
                    game.board[i][j] = None
                    return (i, j)
                game.board[i][j] = None
    return None

def evaluate_move(game, row, col):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    total_score = 0
    
    for dx, dy in directions:
        line = get_line(game, row, col, dx, dy, game.current_player)
        total_score += score_line(line)
        
        # 评估阻止对手的价值
        opponent_line = get_line(game, row, col, dx, dy, 'White' if game.current_player == 'Black' else 'Black')
        total_score += score_line(opponent_line) * 0.8  # 给予稍低的权重
    
    return total_score

def get_line(game, row, col, dx, dy, player):
    line = []
    for i in range(-4, 5):
        r, c = row + i*dx, col + i*dy
        if 0 <= r < 15 and 0 <= c < 15:
            if game.board[r][c] == player:
                line.append(1)
            elif game.board[r][c] is None:
                line.append(0)
            else:
                line.append(-1)
        else:
            line.append(-1)
    return line

def score_line(line):
    score = 0
    length = len(line)
    for i in range(length - 4):
        window = line[i:i+5]
        score += score_window(window)
    return score

def score_window(window):
    if 5 == sum(window):
        return 100000  # 五连
    elif 4 == sum(window) and 0 in window:
        return 10000   # 活四
    elif 3 == sum(window) and window.count(0) == 2:
        return 1000    # 活三
    elif 2 == sum(window) and window.count(0) == 3:
        return 100     # 活二
    elif 1 == sum(window) and window.count(0) == 4:
        return 10      # 活一
    return 0