import os
import re

BACKEND_DIR = r"c:\Users\kirti\OneDrive\Desktop\PROJECTS\scrag\backend"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'print(' not in content:
        return

    # Add logger import if not present
    if 'import logging' not in content:
        # Find where to insert
        imports_end = 0
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                imports_end = i + 1
        
        insert_text = "\nimport logging\nlogger = logging.getLogger(__name__)\n"
        if imports_end > 0:
            lines.insert(imports_end, "import logging")
            lines.insert(imports_end + 1, "logger = logging.getLogger(__name__)")
        else:
            lines.insert(0, "import logging")
            lines.insert(1, "logger = logging.getLogger(__name__)")
        
        content = '\n'.join(lines)

    # Replace print(f"...Error...") with logger.error
    # Replace print(f"...Warning...") with logger.warning
    # Replace print(...) with logger.debug
    
    def replacer(match):
        inner = match.group(1)
        if re.search(r'error|exception|failed\b', inner, re.IGNORECASE):
            return f"logger.error({inner})"
        elif re.search(r'warn', inner, re.IGNORECASE):
            return f"logger.warning({inner})"
        else:
            return f"logger.debug({inner})"

    # Naive replacement for print statements
    new_content = re.sub(r'print\((.*?)\)', replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk(BACKEND_DIR):
    # skip venv, etc
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))

print("Done")
