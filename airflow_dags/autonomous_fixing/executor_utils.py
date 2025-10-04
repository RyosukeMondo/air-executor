"""
Utility functions for executor_runner.py

Extracted to reduce file size and improve maintainability.
"""


def extract_file_context(filepath: str, error_line: int = None, context_lines: int = 10) -> str:
    """Extract minimal relevant context from a file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if error_line is not None and error_line > 0:
            # Get context around error line
            start = max(0, error_line - context_lines - 1)
            end = min(len(lines), error_line + context_lines)

            # Add line numbers
            numbered = []
            for i, line in enumerate(lines[start:end], start=start + 1):
                marker = "→ " if i == error_line else "  "
                numbered.append(f"{marker}{i:4d} | {line}")

            return "".join(numbered)
        # Return file structure (imports + signatures)
        return extract_structure(lines)

    except Exception as e:
        return f"Could not read file: {str(e)}"


def extract_structure(lines: list) -> str:
    """Extract imports and function/class signatures only"""
    structure = []

    def is_structural_line(stripped: str) -> bool:
        """Check if line is import or declaration"""
        starts = ("import ", "export ", "class ", "abstract class ", "mixin ", "enum ")
        contains = ("void ", "Future<", "Stream<")
        return any(stripped.startswith(s) for s in starts) or any(c in stripped for c in contains)

    for line in lines:
        if is_structural_line(line.strip()):
            structure.append(line)

    return "".join(structure) if structure else "// Empty or no structure found"
