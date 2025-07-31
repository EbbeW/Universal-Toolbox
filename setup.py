import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg
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

class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Toolbox Installer")
        self.geometry("712x256")
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

        # Copy toolbox.py to install dir
        src_toolbox = os.path.join(os.path.dirname(__file__), "toolbox.py")
        src_icon = os.path.join(os.path.dirname(__file__), "toolbox.ico")
        src_sync = os.path.join(os.path.dirname(__file__), "sync.py")
        src_uninstall = os.path.join(os.path.dirname(__file__), "uninstall.py")
        
        dst_toolbox = os.path.join(install_dir, "toolbox.py")
        dst_icon = os.path.join(install_dir, "toolbox.ico")
        dst_sync = os.path.join(install_dir, "sync.py")
        dst_uninstall = os.path.join(install_dir, "uninstall.py")
        shutil.copyfile(src_toolbox, dst_toolbox)
        shutil.copyfile(src_sync, dst_sync)
        shutil.copyfile(src_uninstall, dst_uninstall)
        shutil.copyfile(src_icon, dst_icon)

        # Write registry entries
        try:
            self.create_registry(python_path, dst_toolbox, dst_sync)
            messagebox.showinfo("Installed", "Universal Toolbox installed successfully.")
        except Exception as e:
            messagebox.showerror("Registry Error", f"Failed to create context menu: {e}")

        self.destroy()

    def create_registry(self, python_path, toolbox_path, sync_script_path):
        install_dir = self.install_path.get()

        # File (.py) menu
        file_base = 'SystemFileAssociations\\.py\\shell\\UniversalToolboxAdd'
        file_cmd = file_base + '\\command'
        icon_path = install_dir + '\\toolbox.ico'
        
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, file_base) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'Add to Universal Toolbox')
            winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, icon_path)
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, file_cmd) as key:
            cmd = f'"{python_path}" "{toolbox_path}" --add "%1"'
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, cmd)


if __name__ == '__main__':
    InstallerGUI().mainloop()
