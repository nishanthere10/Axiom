import subprocess
import os

app_data_dir = r"C:\Users\kirti\.gemini\antigravity-ide\brain\db245168-4c45-4df8-b215-5a1de90002ab\scratch"
os.makedirs(app_data_dir, exist_ok=True)

try:
    venv_python = r"c:\Users\kirti\OneDrive\Desktop\PROJECTS\scrag\backend\.venv\Scripts\python.exe"
    
    print("Running test_harness.py via subprocess...")
    result = subprocess.run([venv_python, "test_harness.py"], capture_output=True, text=True, cwd=r"c:\Users\kirti\OneDrive\Desktop\PROJECTS\scrag\backend")
    
    out_path = os.path.join(app_data_dir, "harness_output.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
        
    print(f"Execution finished and saved to {out_path}.")
except Exception as e:
    print(f"Failed to execute: {e}")
