"""
Extracts indexable text from source code files.
For code files: extracts public API surface only (signatures + docstrings).
For docs: returns full content truncated to MAX_DOC_CHARS.

Strategy: regex-based extraction. No AST parsing.
Rationale: AST parsers (tree-sitter, libcst) add heavy dependencies.
Regex covers 90% of cases for signature extraction at the scale of a workspace.
"""
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_DOC_CHARS  = 15_000
MAX_CODE_CHARS = 12_000    # code files produce denser summaries

# Extensions grouped by extraction strategy
DOC_EXTENSIONS = {".md", ".mdx", ".txt", ".rst"}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".toml", ".env.example"}
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rs", ".cs", ".rb", ".php"}
SKIP_EXTENSIONS = {".lock", ".png", ".jpg", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".min.js", ".min.css"}

# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "__pycache__",
    ".venv", "venv", "vendor", ".cargo", "target", "coverage",
    ".pytest_cache", ".mypy_cache", ".tox", "migrations",
}

MAX_FILE_BYTES = 100_000   # 100KB hard cap


def should_index(file_path: str, file_size_bytes: int) -> bool:
    """
    Returns True if this file should be indexed.
    Checks: extension allowlist, directory blocklist, size cap.
    """
    p = Path(file_path)

    # Skip based on extension
    suffix = p.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return False

    allowed = DOC_EXTENSIONS | CONFIG_EXTENSIONS | CODE_EXTENSIONS
    if suffix not in allowed:
        return False

    # Skip based on directory
    parts = set(p.parts[:-1])  # all dir components
    if parts & SKIP_DIRS:
        return False

    # Skip oversized files
    if file_size_bytes > MAX_FILE_BYTES:
        logger.debug("Skipping large file %s (%d bytes)", file_path, file_size_bytes)
        return False

    return True


def extract_for_indexing(content: str, file_path: str) -> str:
    """
    Returns the indexable text for a file.
    Code files: signatures + docstrings only.
    Doc/config files: full content (truncated).
    """
    suffix = Path(file_path).suffix.lower()

    if suffix in DOC_EXTENSIONS:
        return content[:MAX_DOC_CHARS]

    if suffix in CONFIG_EXTENSIONS:
        # Config files: strip comments, truncate
        return content[:4_000]

    if suffix in CODE_EXTENSIONS:
        return _extract_code_signatures(content, suffix, file_path)

    return content[:MAX_DOC_CHARS]


def _extract_code_signatures(content: str, ext: str, file_path: str) -> str:
    """
    Extracts public API surface from source code:
    - Class/struct/interface/enum declarations
    - Function/method signatures (not bodies)
    - Module-level docstrings and comments
    - Export statements (TypeScript)
    Skips: function bodies, private members, implementation details.
    """
    try:
        if ext == ".py":
            return _extract_python_signatures(content)
        elif ext in {".ts", ".tsx", ".js", ".jsx"}:
            return _extract_typescript_signatures(content)
        elif ext == ".go":
            return _extract_go_signatures(content)
        elif ext in {".java", ".cs"}:
            return _extract_java_signatures(content)
        elif ext == ".rs":
            return _extract_rust_signatures(content)
        else:
            # Fallback: return first N chars with comments
            return content[:MAX_CODE_CHARS]
    except Exception as e:
        logger.warning("Signature extraction failed for %s: %s", file_path, e)
        return content[:MAX_CODE_CHARS]


def _extract_python_signatures(content: str) -> str:
    """Extracts Python class/function signatures and docstrings."""
    lines = content.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Module-level docstring (first string literal)
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            quote = stripped[:3]
            output.append(line)
            i += 1
            while i < len(lines) and quote not in lines[i]:
                output.append(lines[i])
                i += 1
            if i < len(lines):
                output.append(lines[i])

        # Class definition
        elif re.match(r'^\s*class\s+\w+', line):
            output.append(line)
            # Include class docstring
            i += 1
            if i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped.startswith('"""') or next_stripped.startswith("'''"):
                    quote = next_stripped[:3]
                    output.append(lines[i])
                    i += 1
                    while i < len(lines) and quote not in lines[i]:
                        output.append(lines[i])
                        i += 1
                    if i < len(lines):
                        output.append(lines[i])
            continue

        # Function/method definition (skip bodies)
        elif re.match(r'^\s*(async\s+)?def\s+\w+', line):
            # Skip private functions (single underscore prefix is ok, double is private)
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name and func_name.group(1).startswith('__') and not func_name.group(1).endswith('__'):
                i += 1
                continue
            output.append(line)
            # Include function docstring
            i += 1
            if i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped.startswith('"""') or next_stripped.startswith("'''"):
                    quote = next_stripped[:3]
                    output.append(lines[i])
                    i += 1
                    while i < len(lines) and quote not in lines[i]:
                        output.append(lines[i])
                        i += 1
                    if i < len(lines):
                        output.append(lines[i])
            continue

        # Module-level imports (first 20 lines)
        elif i < 20 and stripped.startswith(("import ", "from ")):
            output.append(line)

        # Type aliases and constants at module level (not indented)
        elif not line.startswith(" ") and not line.startswith("\t") and "=" in line and not stripped.startswith("#"):
            if len(stripped) < 200:
                output.append(line)

        i += 1

    result = "\n".join(output)
    return result[:MAX_CODE_CHARS]


def _extract_typescript_signatures(content: str) -> str:
    """Extracts TypeScript/JavaScript function/class/interface/type signatures."""
    lines = content.splitlines()
    output = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Export statements: functions, classes, interfaces, types, enums, consts
        if re.match(r'^export\s+(default\s+)?(async\s+)?function\s+', stripped):
            # Capture signature line(s) — stop at first {
            sig = stripped
            output.append(sig.split("{")[0].rstrip() + (";"))
        elif re.match(r'^export\s+(abstract\s+)?class\s+', stripped):
            output.append(stripped.split("{")[0].rstrip())
        elif re.match(r'^export\s+(interface|type|enum)\s+', stripped):
            # Include the full block for interface/type (usually short)
            block = [line]
            j = i + 1
            depth = stripped.count("{") - stripped.count("}")
            while j < len(lines) and depth > 0:
                block.append(lines[j])
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
                if j - i > 30:  # cap block length
                    break
            output.extend(block[:30])
        elif re.match(r'^export\s+const\s+\w+', stripped):
            # Exported const — include declaration, not the value
            output.append(stripped.split("=")[0].rstrip() + ";")
        elif stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            # Comments at top level
            if i < 30:
                output.append(line)
        elif stripped.startswith("import ") and i < 25:
            output.append(line)

    result = "\n".join(output)
    return result[:MAX_CODE_CHARS] if result else content[:2000]


def _extract_go_signatures(content: str) -> str:
    """Extracts Go function/type/interface signatures."""
    lines = content.splitlines()
    output = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^func\s+(\(\w+\s+\*?\w+\)\s+)?[A-Z]', stripped):
            # Exported functions (start with capital)
            output.append(stripped.split("{")[0].rstrip())
        elif re.match(r'^type\s+[A-Z]', stripped):
            output.append(stripped.split("{")[0].rstrip())
        elif stripped.startswith("package ") or stripped.startswith("import "):
            output.append(line)
    return "\n".join(output)[:MAX_CODE_CHARS]


def _extract_java_signatures(content: str) -> str:
    """Extracts Java/C# class/method signatures."""
    lines = content.splitlines()
    output = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^(public|protected)\s+(static\s+)?(abstract\s+)?(class|interface|enum|record)\s+', stripped):
            output.append(stripped.split("{")[0].rstrip())
        elif re.match(r'^\s*(public|protected)\s+', stripped) and "(" in stripped and not stripped.startswith("//"):
            output.append(stripped.split("{")[0].rstrip() + ";")
        elif stripped.startswith("package ") or stripped.startswith("import "):
            output.append(line)
    return "\n".join(output)[:MAX_CODE_CHARS]


def _extract_rust_signatures(content: str) -> str:
    """Extracts Rust pub fn/struct/trait/enum signatures."""
    lines = content.splitlines()
    output = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^pub\s+(async\s+)?fn\s+', stripped):
            output.append(stripped.split("{")[0].rstrip() + ";")
        elif re.match(r'^pub\s+(struct|trait|enum|type)\s+', stripped):
            output.append(stripped.split("{")[0].rstrip())
        elif stripped.startswith("use ") or stripped.startswith("mod "):
            output.append(line)
    return "\n".join(output)[:MAX_CODE_CHARS]
