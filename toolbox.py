import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import subprocess
import re
import tempfile

# Constants
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(INSTALL_DIR, "tools")
TOOLBOX_SCRIPT = os.path.abspath(__file__)
ICON = os.path.join(INSTALL_DIR, "toolbox.ico")
PYTHON_EXEC = sys.executable
with open(os.path.join(INSTALL_DIR, "pythonPath.txt")) as f:
    PYTHON_EXEC = f.read()

MODE_FILE = os.path.join(INSTALL_DIR, "mode.flag")
DEFAULT_EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_current_mode():
    try:
        with open(MODE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "run"

def set_app_icon(hwnd=None):
    import ctypes
    import ctypes.wintypes
    appid = "Universal.Toolbox"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    if hwnd:
        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, ICON)


def normalise_name(name):
    return re.sub(r'[^A-Za-z0-9_]', '', name.replace(" ", ""))

def get_existing_categories():
    if not os.path.isdir(TOOLS_DIR):
        return []
    return [
        open(os.path.join(TOOLS_DIR, d, 'friendlyname.txt'), encoding='utf-8').read().strip()
        for d in os.listdir(TOOLS_DIR)
        if os.path.isdir(os.path.join(TOOLS_DIR, d)) and os.path.isfile(os.path.join(TOOLS_DIR, d, 'friendlyname.txt'))
    ]

def add_tool_interface(source_script):
    os.makedirs(TOOLS_DIR, exist_ok=True)
    
    with open(source_script, 'r', encoding='utf-8') as f:
        source_code = f.read()

    name, desc, _ = extract_metadata_and_globals(source_code)
    
    root = tk.Tk()
    set_app_icon(root.winfo_id())
    root.iconbitmap(ICON)
    root.title("Add to Universal Toolbox")
    root.geometry("500x250")

    base_filename = os.path.splitext(os.path.basename(source_script))[0]
    tool_name = tk.StringVar(value=name or base_filename)
    category = tk.StringVar()
    description = tk.StringVar(value=desc or "")

    categories = get_existing_categories()

    ttk.Label(root, text="Tool Name:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ttk.Entry(root, textvariable=tool_name, width=40).grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(root, text="Category:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    cat_input = ttk.Combobox(root, textvariable=category, values=categories)
    cat_input.set("")
    cat_input.grid(row=1, column=1, padx=10, pady=10)
    cat_input['state'] = 'normal'

    ttk.Label(root, text="Description:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ttk.Entry(root, textvariable=description, width=40).grid(row=2, column=1, padx=10, pady=10)

    def on_submit():
        name = tool_name.get().strip()
        cat = category.get().strip()
        desc = description.get().strip()

        if not name or not cat:
            messagebox.showerror("Error", "Tool name and category are required.")
            return

        norm_cat = normalise_name(cat)
        norm_name = normalise_name(name)

        category_path = os.path.join(TOOLS_DIR, norm_cat)
        os.makedirs(category_path, exist_ok=True)

        with open(os.path.join(category_path, "friendlyname.txt"), "w", encoding="utf-8") as f:
            f.write(cat)

        dest_path = os.path.join(category_path, f"{norm_name}.py")

        with open(source_script, 'r', encoding='utf-8') as src:
            lines = src.readlines()

        new_lines = []
        name_written = False
        desc_written = False

        for line in lines:
            if line.startswith("#NAME:"):
                new_lines.append(f"#NAME: {name}\n")
                name_written = True
            elif line.startswith("#DESCRIPTION:"):
                new_lines.append(f"#DESCRIPTION: {desc}\n")
                desc_written = True
            else:
                new_lines.append(line)

        if not name_written:
            new_lines.insert(0, f"#NAME: {name}\n")
        if not desc_written:
            new_lines.insert(1 if name_written else 0, f"#DESCRIPTION: {desc}\n")

        with open(dest_path, 'w', encoding='utf-8') as dst:
            dst.writelines(new_lines)

        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "sync.py")])
        messagebox.showinfo("Success", f"Tool '{name}' added to category '{cat}'.")
        root.destroy()

    ttk.Button(root, text="Add Tool", command=on_submit).grid(row=3, column=1, pady=20)
    root.mainloop()

def extract_metadata_and_globals(source_code):
    lines = source_code.splitlines()
    name = ""
    description = ""
    variables = {}

    for line in lines:
        if line.startswith("#NAME:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("#DESCRIPTION:"):
            description = line.split(":", 1)[1].strip()
        elif re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line):
            var_name, value = line.split("=")
            variables[var_name.strip()] = value.strip()
    
    return name, description, variables

def prompt_inputs_and_run(script_path, context_arg=None):
    with open(script_path, "r", encoding="utf-8") as f:
        source = f.read()

    name, desc, variables = extract_metadata_and_globals(source)

    input_values = {}
    run_triggered = [False]  # mutable closure var


    def launch_gui():
        window = tk.Tk()
        window.title(name or "Tool Inputs")
        set_app_icon(window.winfo_id())
        window.iconbitmap(ICON)
        window.geometry("500x500+" + str(window.winfo_screenwidth()//2 - 250) + "+200")

        ttk.Label(window, text=desc, font=("Arial", 10, "italic"), wraplength=450).grid(row=0, column=0, columnspan=2, pady=(10, 10))

        for i, (var, default) in enumerate(variables.items()):
            ttk.Label(window, text=var + " =").grid(row=i + 1, column=0, padx=10, pady=5, sticky="e")
            var_str = tk.StringVar(value=str(default))
            entry = ttk.Entry(window, width=40, textvariable=var_str)
            entry.grid(row=i + 1, column=1, padx=10, pady=5)
            input_values[var] = var_str


        def on_run():
            run_triggered[0] = True
            window.destroy()
        
        window.protocol("WM_DELETE_WINDOW", window.destroy)  # Don't run on X

        ttk.Button(window, text="Run", command=on_run).grid(row=len(variables)+2, column=1, pady=20)
        window.mainloop()


    launch_gui()
    
    if not run_triggered[0]:
            return  # User closed the window, don't run the tool

    # Replace variables in source
    modified = []
    for line in source.splitlines():
        replaced = False
        for var, var_str in input_values.items():
            if re.match(fr'^{var}\s*=', line):
                modified.append(f"{var} = {var_str.get().strip()}")
                replaced = True
                break
        if not replaced:
            modified.append(line)

    # Write and run the modified script
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
        tmp.write("\n".join(modified))
        tmp_path = tmp.name
    
    cwd = None
    if context_arg:
        if os.path.isdir(context_arg):
            cwd = context_arg
        elif os.path.isfile(context_arg):
            cwd = os.path.dirname(context_arg)
            
    subprocess.run([PYTHON_EXEC, tmp_path], check=False, cwd=cwd)

def invoke_tool(relative_path):
    context = None
    if "--context" in sys.argv:
        i = sys.argv.index("--context")
        if i + 1 < len(sys.argv):
            context = sys.argv[i + 1]

    full_path = os.path.join(TOOLS_DIR, relative_path)
    if not os.path.exists(full_path):
        print("Tool not found.")
        return

    mode = get_current_mode()

    if mode == "run":
        prompt_inputs_and_run(full_path, context)

    elif mode == "delete":
        # Create a hidden root just for dialogs
        root = tk.Tk()
        root.withdraw()
        set_app_icon(root.winfo_id())
        root.iconbitmap(ICON)
        


        confirm = messagebox.askyesno("Delete Tool", f"Are you sure you want to delete this tool?\n\n{relative_path}")
        if confirm:
            os.remove(full_path)
            cat_dir = os.path.dirname(full_path)
            if not any(os.scandir(cat_dir)):
                os.remove(os.path.join(cat_dir, "friendlyname.txt"))
                os.rmdir(cat_dir)
            subprocess.run([PYTHON_EXEC, os.path.join(INSTALL_DIR, "sync.py")])
            messagebox.showinfo("Deleted", "Tool deleted successfully.")

        root.destroy()

    elif mode == "export":
        # Create a hidden root just for dialogs
        root = tk.Tk()
        root.withdraw()
        set_app_icon(root.winfo_id())
        root.iconbitmap(ICON)
        


        import tkinter.filedialog as fd

        default_name = os.path.splitext(os.path.basename(full_path))[0]
        export_folder = fd.askdirectory(initialdir=DEFAULT_EXPORT_DIR, title="Select Export Folder")
        if not export_folder:
            root.destroy()
            return

        export_name = tk.simpledialog.askstring("Export Tool", "Export file name (without .py):", initialvalue=default_name)
        if not export_name:
            root.destroy()
            return

        with open(full_path, 'r', encoding='utf-8') as src:
            content = src.read()

        export_path = os.path.join(export_folder, f"{normalise_name(export_name)}.py")
        with open(export_path, 'w', encoding='utf-8') as dst:
            dst.write(content)

        messagebox.showinfo("Exported", f"Tool exported as:\n{export_path}\n\nMetadata preserved.")
        root.destroy()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--add":
        if len(sys.argv) < 3:
            print("Usage: toolbox.py --add <script.py>")
        else:
            add_tool_interface(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "--run":
        if len(sys.argv) < 3:
            print("Usage: toolbox.py --run <category/tool.py>")
        else:
            invoke_tool(sys.argv[2])
    else:
        print("Usage:")
        print("  toolbox.py --add <script.py>")
        print("  toolbox.py --run <category/tool.py> [--context <path>]")

if __name__ == "__main__":
    main()
