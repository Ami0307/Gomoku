import os
import sys

def resource_path(relative_path):
    """获取资源的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 设置环境变量，让其他模块可以使用这个函数
os.environ['RESOURCE_PATH'] = resource_path('')

from game_logic import game_loop

def main():
    game_loop()

if __name__ == "__main__":
    main()
