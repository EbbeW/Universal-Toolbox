import os
import shutil
import winreg
import ctypes
import sys

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def delete_registry_tree(root, subkey):
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            _delete_subkeys_recursively(key, subkey)
        winreg.DeleteKey(root, subkey)
        print(f"✅ Deleted registry key: {subkey}")
    except FileNotFoundError:
        print(f"ℹ️ Registry key not found: {subkey}")
    except Exception as e:
        print(f"❌ Failed to delete registry key: {subkey}\n{e}")

def _delete_subkeys_recursively(key, current_path):
    try:
        i = 0
        while True:
            subkey_name = winreg.EnumKey(key, i)
            full_subkey_path = current_path + "\\" + subkey_name
            delete_registry_tree(winreg.HKEY_CLASSES_ROOT, full_subkey_path)
            i += 1
    except OSError:
        pass  # No more subkeys

def uninstall():
    if not is_admin():
        print("You need to run this script as admin")
        sys.exit()

    print("🔧 Uninstalling Universal Toolbox...")

    # Main context menu (tool launcher)
    delete_registry_tree(winreg.HKEY_CLASSES_ROOT, r'Directory\Background\shell\UniversalToolbox')

    # .py file "Add to Toolbox" menu
    delete_registry_tree(winreg.HKEY_CLASSES_ROOT, r'SystemFileAssociations\.py\shell\UniversalToolboxAdd')

    # Delete toolbox folder
    if os.path.exists(INSTALL_DIR):
        try:
            shutil.rmtree(INSTALL_DIR)
            print(f"✅ Deleted toolbox folder: {INSTALL_DIR}")
        except Exception as e:
            print(f"❌ Failed to delete toolbox folder:\n{e}")
    else:
        print(f"ℹ️ Toolbox folder not found: {INSTALL_DIR}")

    print("\n🗑️ Universal Toolbox successfully uninstalled.")

if __name__ == "__main__":
    uninstall()