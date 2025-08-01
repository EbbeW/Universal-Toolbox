import os
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("You need to run this script with admin permissions.")
    sys.exit()

DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "universal-toolbox")

def get_python_paths():
    """Try to find Python interpreters in PATH or common places"""
    possible = []
    for path in os.environ.get("PATH", "").split(";"):
        if os.path.exists(os.path.join(path, "python.exe")):
            possible.append(os.path.join(path, "python.exe"))
    return sorted(set(possible))

def set_app_icon(hwnd=None):
    import ctypes
    import ctypes.wintypes
    appid = "Universal.Toolbox"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    if hwnd:
        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, os.path.join(os.path.dirname(__file__), "toolbox.ico"))

class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Toolbox Installer")
        self.geometry("712x256")
        set_app_icon(self.winfo_id())
        self.iconbitmap(os.path.join(os.path.dirname(__file__), "toolbox.ico"))
        self.resizable(False, False)

        self.python_path = tk.StringVar(value=sys.executable)
        self.install_path = tk.StringVar(value=DEFAULT_INSTALL_DIR)

        self.create_widgets()

    def create_widgets(self):
        padding = {'padx': 10, 'pady': 10}

        ttk.Label(self, text="Select Python Interpreter:").grid(row=0, column=0, sticky="w", **padding)
        entry = ttk.Entry(self, textvariable=self.python_path, width=60)
        entry.grid(row=0, column=1, **padding)

        ttk.Button(self, text="Browse", command=self.browse_python).grid(row=0, column=2, **padding)

        ttk.Label(self, text="Install Location:").grid(row=1, column=0, sticky="w", **padding)
        ttk.Entry(self, textvariable=self.install_path, width=60).grid(row=1, column=1, **padding)
        ttk.Button(self, text="Browse", command=self.browse_folder).grid(row=1, column=2, **padding)

        ttk.Button(self, text="Install", command=self.install).grid(row=3, column=1, pady=20)

    def browse_python(self):
        path = filedialog.askopenfilename(title="Select Python Interpreter", filetypes=[("Python", "python.exe")])
        if path:
            self.python_path.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title="Choose install folder")
        if path:
            self.install_path.set(path)

    def install(self):
        python_path = self.python_path.get()
        install_dir = self.install_path.get()

        if not os.path.isfile(python_path) or not python_path.endswith("python.exe"):
            messagebox.showerror("Invalid Python", "Please select a valid python.exe")
            return

        os.makedirs(install_dir, exist_ok=True)
        tools_dir = os.path.join(install_dir, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        
        to_copy = ["toolbox.py", "sync.py", "uninstall.py", "toolbox.ico", "elevate_mode.py"]
        for file in to_copy:
            src = os.path.join(os.path.dirname(__file__), file)
            dst = os.path.join(install_dir, file)
            shutil.copyfile(src, dst)
        
        with open(os.path.join(install_dir, "pythonPath.txt"), "w") as f:
            f.write(python_path)
        
        with open(os.path.join(install_dir, "mode.flag"), "w") as f:
            f.write("run")

        # Write registry entries
        try:
            self.create_registry(python_path, install_dir)
            messagebox.showinfo("Installed", "Universal Toolbox installed successfully.")
        except Exception as e:
            messagebox.showerror("Registry Error", f"Failed to create context menu: {e}")

        self.destroy()

    def create_registry(self, python_path, install_dir):
        subprocess.run([python_path, f"{install_dir}\\sync.py"], check=True)


if __name__ == '__main__':
    InstallerGUI().mainloop()
