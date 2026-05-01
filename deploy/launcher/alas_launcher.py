"""
ALAS Launcher - 系统托盘管理器
开机自启，管理 MCP Server + ALAS.bat，支持右键菜单操作。

路径检测逻辑：
  - 作为 PyInstaller exe 运行时：exe 在 ALAS 根目录，直接使用
  - 作为脚本运行时：脚本在 deploy/launcher/，向上两级到 ALAS 根目录
  - 可通过环境变量 ALAS_DIR 覆盖

图标：与 ALAS 保持一致，使用 deploy/launcher/icon.ico

依赖：pystray, Pillow
打包：pyinstaller --onefile --windowed --icon deploy/launcher/icon.ico --name alas_launcher deploy/launcher/alas_launcher.py
  （输出 exe 到 ALAS 根目录）
"""

import ctypes
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# 路径检测
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # PyInstaller exe 模式 — exe 在 ALAS 根目录
    EXE_DIR = Path(sys.executable).parent
    ALAS_DIR = EXE_DIR
    RESOURCE_DIR = EXE_DIR          # icon.ico 与 exe 同目录
else:
    # 脚本模式 — 脚本在 deploy/launcher/，ALAS 根目录在两级之上
    SCRIPT_DIR = Path(__file__).parent.resolve()
    RESOURCE_DIR = SCRIPT_DIR       # icon.ico 与脚本同目录
    ALAS_DIR = SCRIPT_DIR.parent.parent.resolve()

ALAS_DIR = Path(os.getenv("ALAS_DIR", str(ALAS_DIR)))
ALAS_BAT = ALAS_DIR / "ALAS.bat"
MCP_SERVER = ALAS_DIR / "mcp_server.py"
# MCP Server 使用系统 Python（PyInstaller exe 不包含 mcp 包）
MCP_PYTHON = Path(os.getenv(
    "MCP_PYTHON",
    r"C:\Program Files\Python313\python.exe",
))
ALAS_API_URL = "http://127.0.0.1:22267"


# ---------------------------------------------------------------------------
# 图标加载（使用 ALAS 图标）
# ---------------------------------------------------------------------------
def get_icon_path():
    """返回 icon.ico 的绝对路径"""
    return RESOURCE_DIR / "icon.ico"


def create_icon(width=64, height=64):
    """
    加载 ALAS icon.ico 作为托盘图标。
    如果 icon.ico 不存在，回退到程序生成的图标。
    """
    icon_path = get_icon_path()
    if icon_path.exists():
        try:
            return Image.open(str(icon_path)).resize((width, height))
        except Exception as e:
            print(f"[Launcher] 加载图标失败: {e}，使用默认图标")

    # 回退：生成简单图标
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([4, 4, width - 4, height - 4], fill=(70, 130, 200, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "A", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        ((width - tw) // 2, (height - th) // 2 - 4),
        "A",
        fill=(255, 255, 255, 255),
        font=font,
    )
    return image


# ---------------------------------------------------------------------------
# 子进程管理
# ---------------------------------------------------------------------------
class ProcessManager:
    def __init__(self):
        self.alas_proc = None
        self.mcp_proc = None
        self.mcp_thread = None

    def start_alas(self):
        if self.alas_proc is not None and self.alas_proc.poll() is None:
            print("[Launcher] ALAS 已在运行")
            return
        if not ALAS_BAT.exists():
            print(f"[Launcher] 找不到 {ALAS_BAT}，跳过 ALAS 启动")
            return
        print(f"[Launcher] 启动 ALAS: {ALAS_BAT}")
        self.alas_proc = subprocess.Popen(
            str(ALAS_BAT),
            cwd=str(ALAS_DIR),
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

    def stop_alas(self):
        if self.alas_proc is not None and self.alas_proc.poll() is None:
            print("[Launcher] 停止 ALAS...")
            self.alas_proc.terminate()
            try:
                self.alas_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.alas_proc.kill()
        self.alas_proc = None

    def restart_alas(self):
        print("[Launcher] 重启 ALAS...")
        self.stop_alas()
        time.sleep(2)
        self.start_alas()

    def start_mcp(self):
        if self.mcp_thread is not None and self.mcp_thread.is_alive():
            print("[Launcher] MCP Server 已在运行")
            return
        if not MCP_SERVER.exists():
            print(f"[Launcher] 找不到 {MCP_SERVER}，跳过 MCP 启动")
            return

        def _run_mcp():
            print(f"[Launcher] 启动 MCP Server: {MCP_SERVER}")
            env = os.environ.copy()
            env["ALAS_API_BASE"] = ALAS_API_URL
            self.mcp_proc = subprocess.Popen(
                [str(MCP_PYTHON), str(MCP_SERVER)],
                cwd=str(ALAS_DIR),
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            self.mcp_proc.wait()
            print("[Launcher] MCP Server 已退出")

        self.mcp_thread = threading.Thread(target=_run_mcp, daemon=True)
        self.mcp_thread.start()

    def stop_mcp(self):
        if self.mcp_proc is not None and self.mcp_proc.poll() is None:
            print("[Launcher] 停止 MCP Server...")
            self.mcp_proc.terminate()
            try:
                self.mcp_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mcp_proc.kill()
        self.mcp_proc = None

    def restart_mcp(self):
        print("[Launcher] 重启 MCP Server...")
        self.stop_mcp()
        time.sleep(1)
        self.start_mcp()

    def stop_all(self):
        print("[Launcher] 停止所有子进程...")
        self.stop_alas()
        self.stop_mcp()


pm = ProcessManager()

# ---------------------------------------------------------------------------
# 单实例检测（socket 绑定法，跨平台）
# ---------------------------------------------------------------------------
SINGLE_INSTANCE_PORT = 22999  # ALAS Launcher 专用端口

def ensure_single_instance() -> socket.socket | None:
    """
    确保只有一个 Launcher 实例运行。
    返回 server_socket（首次启动）或 None（已在运行，已提示并退出）。
    """
    # 先尝试连接，看是否已有实例
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(1)
        result = probe.connect_ex(("127.0.0.1", SINGLE_INSTANCE_PORT))
        if result == 0:
            # 端口已绑定，说明已有实例在运行
            probe.close()
            _notify_already_running()
            sys.exit(0)
        probe.close()
    except Exception:
        pass

    # 没有实例运行，绑定端口占位
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        server_sock.listen(1)
        print(f"[Launcher] 单实例锁已获取 (port {SINGLE_INSTANCE_PORT})")
        return server_sock
    except OSError as e:
        # 绑定失败，说明已有实例
        _notify_already_running()
        sys.exit(0)


def _notify_already_running():
    """提示用户 Launcher 已在运行（Windows 弹窗 + 控制台）"""
    msg = "ALAS Launcher 已经在运行中，无法重复启动。"
    print(f"[Launcher] {msg}")
    # Windows 弹窗提示
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "ALAS Launcher 已经在运行！\n\n请检查系统托盘区域（右下角）。",
                "ALAS Launcher",
                0x40,  # MB_ICONINFORMATION
            )
        except Exception:
            pass


single_instance_sock = None  # 持有 socket 保持单实例锁


def release_single_instance():
    """释放单实例锁"""
    global single_instance_sock
    if single_instance_sock is not None:
        try:
            single_instance_sock.close()
        except Exception:
            pass
        single_instance_sock = None
        print("[Launcher] 单实例锁已释放")


# ---------------------------------------------------------------------------
# 托盘菜单
# ---------------------------------------------------------------------------
def on_restart_alas(icon, item):
    pm.restart_alas()
    icon.notify("ALAS 正在重启...", "ALAS Launcher")


def on_restart_mcp(icon, item):
    pm.restart_mcp()
    icon.notify("MCP Server 正在重启...", "ALAS Launcher")


def on_open_webui(icon, item):
    webbrowser.open(ALAS_API_URL)


def on_open_log(icon, item):
    log_dir = ALAS_DIR / "log"
    if log_dir.exists():
        os.startfile(str(log_dir))


def on_exit(icon, item):
    print("[Launcher] 退出中...")
    pm.stop_all()
    release_single_instance()
    icon.stop()


def build_menu():
    return pystray.Menu(
        pystray.MenuItem("重启 ALAS", on_restart_alas),
        pystray.MenuItem("重启 MCP Server", on_restart_mcp),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("打开 WebUI", on_open_webui),
        pystray.MenuItem("打开日志目录", on_open_log),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_exit),
    )


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    global single_instance_sock

    print("=" * 60)
    print("  ALAS Launcher v0.1.0 - 系统托盘管理器")
    print("=" * 60)
    print(f"ALAS 目录: {ALAS_DIR}")
    print(f"MCP Python: {MCP_PYTHON}")
    print()

    # 0. 单实例检测（必须在最前面，最先执行）
    single_instance_sock = ensure_single_instance()
    # ensure_single_instance() 在检测到已有实例时会直接 sys.exit(0)，不会返回

    # 1. 先启动 MCP Server
    pm.start_mcp()
    time.sleep(2)

    # 2. 再启动 ALAS.bat
    pm.start_alas()
    time.sleep(3)

    # 3. 系统托盘
    icon = pystray.Icon(
        "alas_launcher",
        icon=create_icon(),
        menu=build_menu(),
        title="ALAS Launcher",
    )
    print("[Launcher] 系统托盘已启动，右键图标进行操作")
    icon.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Launcher] 收到退出信号")
        release_single_instance()
        pm.stop_all()
        sys.exit(0)
