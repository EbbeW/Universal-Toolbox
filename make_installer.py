import base64
import os


ASSETS = ["toolbox.py", "sync.py", "setup.py", "uninstall.py", "toolbox.ico"]
RUN_SCRIPT = "setup.py"
OUT_SCRIPT = "install_toolbox.py"

def encode_file(filepath):
    with open(filepath, "rb") as f:
        content = f.read()

    if os.path.basename(filepath) == RUN_SCRIPT:
        injection = f"""
import os
import atexit

def cleanup_flag():
    try:
        os.remove("install_complete.flag")
    except Exception:
        pass

atexit.register(cleanup_flag)
"""
        try:
            decoded = content.decode("utf-8")
            content = (injection + "\n" + decoded).encode("utf-8")
        except UnicodeDecodeError:
            print(f"⚠️ Could not decode {filepath}, skipping flag injection.")
    return base64.b64encode(content).decode("utf-8")

def make_installer():
    # Encode all scripts
    encoded_scripts = {filename: encode_file(filename) for filename in ASSETS}

    with open(OUT_SCRIPT, "w", encoding="utf-8") as out:
        out.write("# Self-extracting installer for Universal Toolbox\n")
        out.write("import base64, os, tempfile, subprocess, time, shutil, sys\n\n")
        out.write("scripts = {\n")
        for name, encoded in encoded_scripts.items():
            out.write(f"    {repr(name)}: '''{encoded}''',\n")
        out.write("}\n\n")
        out.write("""

def run_as_admin(script_path, cwd):
    import ctypes
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', cwd, 1)

def try_rmtree_with_retries(path, delay=1):
    for _ in range(20):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            time.sleep(delay)

def main():
    tmpdir = tempfile.mkdtemp()
    flag_path = os.path.join(tmpdir, "install_complete.flag")

    try:
        for name, b64 in scripts.items():
            with open(os.path.join(tmpdir, name), 'wb') as f:
                f.write(base64.b64decode(b64.encode('utf-8')))

        # Create flag file
        with open(flag_path, "w") as f:
            f.write("waiting")

        print("🔧 Launching setup with admin rights...")
        setup_path = os.path.join(tmpdir, "setup.py")
        run_as_admin(setup_path, cwd=tmpdir)

        print("⏳ Waiting for setup to complete...")
        while os.path.exists(flag_path):
            time.sleep(1)

        print("✅ Setup finished. Cleaning up...")

    finally:
        try_rmtree_with_retries(tmpdir)
        print("🧹 Temp directory cleaned.")
        input("(press enter to exit)")

if __name__ == '__main__':
    main()
""")

    print(f"✅ Installer created at: {OUT_SCRIPT}")
    input("(press enter to exit)")

make_installer()
