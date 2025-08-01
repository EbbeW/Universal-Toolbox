import os
import sys
import tkinter as tk
from tkinter import messagebox

MODE_FILE = os.path.join(os.path.dirname(__file__), "mode.flag")
ICON = os.path.join(os.path.dirname(__file__), "toolbox.ico")

VALID_MODES = {
    "--exp": "export",
    "--del": "delete"
}

def get_current_mode():
    if not os.path.exists(MODE_FILE):
        return "run"
    with open(MODE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def set_mode(new_mode):
    with open(MODE_FILE, "w", encoding="utf-8") as f:
        f.write(new_mode)

def clear_mode():
    set_mode("run")

def set_app_icon(hwnd=None):
    import ctypes
    import ctypes.wintypes
    appid = "Universal.Toolbox"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    if hwnd:
        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, ICON)

def activate_mode(mode_flag):
    if mode_flag not in VALID_MODES:
        print("Usage: elevate_mode.py [--exp | --del]")
        sys.exit(1)

    new_mode = VALID_MODES[mode_flag]
    current_mode = get_current_mode()

    if current_mode != "run":
        messagebox.showwarning("Mode already active", f"Cannot activate {new_mode} mode while '{current_mode}' mode is active.")
        return

    set_mode(new_mode)

    root = tk.Tk()
    root.title(f"{new_mode.capitalize()} Mode Active")
    set_app_icon(root.winfo_id())
    root.iconbitmap(ICON)
    root.geometry("400x200")
    root.protocol("WM_DELETE_WINDOW", lambda: (clear_mode(), root.destroy()))

    msg = (
        f"{new_mode.capitalize()} mode is now active.\n\n"
        f"You can now {new_mode} your tools by browsing the Toolbox as normally "
        f"and selecting a tool.\n\n"
        f"Keep this window open. {new_mode} mode will automatically exit when it's closed."
    )

    tk.Label(root, text=msg, wraplength=360, justify="left").pack(padx=20, pady=20)
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: elevate_mode.py [--exp | --del]")
        sys.exit(1)
    activate_mode(sys.argv[1])
