"""
Lightweight .gitignore pattern matcher.
Parses a .gitignore file and tests whether a path should be excluded.
Does NOT support full glob spec — handles the 95% common cases.
"""
import re
from pathlib import PurePosixPath
from typing import Optional


def _pattern_to_regex(pattern: str) -> Optional[re.Pattern]:
    """Convert a single .gitignore pattern line to a compiled regex."""
    pattern = pattern.strip()
    if not pattern or pattern.startswith("#"):
        return None
    if pattern.startswith("!"):
        return None  # negation patterns not supported — ignore them
    if pattern.startswith("/"):
        pattern = pattern[1:]

    # Escape regex special chars except * and ?
    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\*\*", ".*")
    escaped = escaped.replace(r"\*", "[^/]*")
    escaped = escaped.replace(r"\?", "[^/]")

    if not pattern.endswith("/"):
        # Match both file and directory with this name
        return re.compile(f"(^|/){escaped}(/|$)")
    else:
        return re.compile(f"(^|/){escaped[:-2]}/")


class GitignoreFilter:
    def __init__(self, gitignore_content: str):
        self._patterns = []
        for line in gitignore_content.splitlines():
            rx = _pattern_to_regex(line)
            if rx:
                self._patterns.append(rx)

    def should_ignore(self, path: str) -> bool:
        """Returns True if the path matches any .gitignore pattern."""
        normalized = path.replace("\\", "/")
        return any(rx.search(normalized) for rx in self._patterns)

    @classmethod
    def empty(cls) -> "GitignoreFilter":
        return cls("")
