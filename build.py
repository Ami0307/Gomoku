import PyInstaller.__main__
import os
import sys

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义图标文件路径（如果有的话）
# icon_file = os.path.join(current_dir, 'icon.icns')  # macOS 需要 .icns 格式的图标

# 定义需要打包的数据文件
datas = [
    ("fonts", "fonts"),
    ("sounds", "sounds")
]

# 构建 datas 参数
datas_args = []
for src, dst in datas:
    src_path = os.path.join(current_dir, src)
    if os.path.exists(src_path):
        datas_args.extend(["--add-data", f"{src_path}{os.pathsep}{dst}"])

# PyInstaller 参数
args = [
    "main.py",
    "--onefile",  # 打包成单个文件
    "--windowed",  # 使用 GUI 模式，不显示控制台
    "--clean",  # 清理临时文件
    "--name", "五子棋",
    *datas_args,
    "--debug", "all",  # 添加调试信息
]

# 如果有图标文件，添加图标参数
# if os.path.exists(icon_file):
#     args.extend(['--icon', icon_file])

# 执行打包
PyInstaller.__main__.run(args)