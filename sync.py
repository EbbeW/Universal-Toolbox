# sync.py
import os
import winreg
import re
import sys
import ctypes


INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(INSTALL_DIR, "tools")
PYTHON_EXEC = sys.executable
with open(os.path.join(INSTALL_DIR, "pythonPath.txt")) as f:
    PYTHON_EXEC = f.read()
PYTHON_EXEC_NO_WINDOW = PYTHON_EXEC.replace("python.exe", "pythonw.exe")
TOOLBOX_SCRIPT = os.path.join(INSTALL_DIR, "toolbox.py")
ICON = os.path.join(INSTALL_DIR, "toolbox.ico")

REG_BASE_DIR = "Directory\\Background\\shell\\UniversalToolbox"
REG_BASE_CMD = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\CommandStore\\shell\\UniversalToolbox"
REG_BASE_EXT = "SystemFileAssociations\\.py\\shell\\UniversalToolboxAdd"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Relaunch with admin rights if needed
if not is_admin():
    params = ' '.join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1)
    sys.exit()

def normalise(name):
    return re.sub(r'[^A-Za-z0-9_]', '', name.replace(" ", ""))

def read_friendly_name(path):
    try:
        with open(os.path.join(path, "friendlyname.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def read_tool_name(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#NAME:"):
                    return line.split(":", 1)[1].strip()
    except:
        pass
    return os.path.splitext(os.path.basename(path))[0]

def list_registered_keys(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path) as key:
            return [winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0])]
    except FileNotFoundError:
        return []

def delete_registry_tree(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, winreg.KEY_ALL_ACCESS) as key:
            for sub in list_registered_keys(path):
                delete_registry_tree(f"{path}\\{sub}")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, path)
    except FileNotFoundError:
        pass

def ensure_key(path, root, values, command=None) -> None:
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT if root else winreg.HKEY_LOCAL_MACHINE, path) as key:
        for name, (regtype, val) in values.items():
            winreg.SetValueEx(key, name, 0, regtype, val)
    if command:
        ensure_key(f"{path}\\command", root, {"": (winreg.REG_SZ, command)})

def sync_registry():

    delete_registry_tree(REG_BASE_DIR)
    delete_registry_tree(REG_BASE_EXT)
    delete_registry_tree(REG_BASE_CMD)

    # .py extension: right-click "Add to Universal Toolbox"
    ensure_key(REG_BASE_EXT, True, {
        "MUIVerb": (winreg.REG_SZ, "Add to Universal Toolbox"),
        "Icon": (winreg.REG_SZ, ICON)
    }, command=f'"{PYTHON_EXEC_NO_WINDOW}" "{TOOLBOX_SCRIPT}" --add "%1"')

    # Main context menu entry in "Directory\\Background"
    categories = []
    tools = []
    tool_commands = []

    # Predefined actions
    ensure_key(f"{REG_BASE_CMD}\\Actions\\DeleteTool", False, {
        "MUIVerb": (winreg.REG_SZ, "Delete Tools"),
        "Icon": (winreg.REG_SZ, ICON)
    }, command=f'"{PYTHON_EXEC_NO_WINDOW}" "{INSTALL_DIR}\\elevate_mode.py" --del')

    ensure_key(f"{REG_BASE_CMD}\\Actions\\ExportTool", False, {
        "MUIVerb": (winreg.REG_SZ, "Export/Share Tools"),
        "Icon": (winreg.REG_SZ, ICON)
    }, command=f'"{PYTHON_EXEC_NO_WINDOW}" "{INSTALL_DIR}\\elevate_mode.py" --exp')

    ensure_key(f"{REG_BASE_CMD}\\Actions\\OpenToolboxDir", False, {
        "MUIVerb": (winreg.REG_SZ, "Open Install Directory"),
        "Icon": (winreg.REG_SZ, ICON)
    }, command=f'cmd.exe /c start "" "{INSTALL_DIR}"')

    for category_folder in os.listdir(TOOLS_DIR):
        category_path = os.path.join(TOOLS_DIR, category_folder)
        if not os.path.isdir(category_path):
            continue

        friendly_name = read_friendly_name(category_path)
        if not friendly_name:
            continue

        norm_cat = normalise(friendly_name)
        categories.append(f"UniversalToolbox\\Categories\\{norm_cat}")

        tool_subcommands = []

        for file in os.listdir(category_path):
            if not file.endswith(".py"):
                continue

            tool_path = os.path.join(category_path, file)
            tool_friendly = read_tool_name(tool_path)
            norm_tool = normalise(tool_friendly)
            tool_id = f"{norm_cat}_{norm_tool}"
            tool_key = f"{REG_BASE_CMD}\\Tools\\{tool_id}"
            tools.append(tool_key)
            tool_subcommands.append(f"UniversalToolbox\\Tools\\{tool_id}")

            ensure_key(tool_key, False, {
                "MUIVerb": (winreg.REG_SZ, tool_friendly),
            }, command=f'"{PYTHON_EXEC_NO_WINDOW}" "{TOOLBOX_SCRIPT}" --run "{category_folder}/{file}" --context "%V"')

        # Write the category entry pointing to its tools
        cat_key = f"{REG_BASE_CMD}\\Categories\\{norm_cat}"
        ensure_key(cat_key, False, {
            "MUIVerb": (winreg.REG_SZ, friendly_name),
            "SubCommands": (winreg.REG_SZ, ";".join(tool_subcommands))
        })

    # Compose SubCommands entry for the top-level right-click menu
    subcommands = [
        "UniversalToolbox\\Actions\\ExportTool",
        "UniversalToolbox\\Actions\\DeleteTool",
        "UniversalToolbox\\Actions\\OpenToolboxDir",
        "|",  # separator
    ] + categories

    ensure_key(REG_BASE_DIR, True, {
        "MUIVerb": (winreg.REG_SZ, "Universal Toolbox"),
        "SubCommands": (winreg.REG_SZ, ";".join(subcommands)),
        "Icon": (winreg.REG_SZ, ICON)
    })

    print("✅ Registry sync complete.")


if __name__ == "__main__":
    sync_registry()
