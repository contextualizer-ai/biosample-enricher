#!/usr/bin/env python3
"""
Generate alphabetical index of all public functions and methods.

This script scans the biosample_enricher package and creates a comprehensive
alphabetical index of all public functions and methods with their signatures
and descriptions.

Usage:
    python scripts/generate_api_index.py [--output docs/API_INDEX.md]
"""

import argparse
import ast
from collections import defaultdict
from pathlib import Path
from typing import Any


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to extract function and method definitions, plus module constants."""

    def __init__(self, module_path: str):
        self.module_path = module_path
        self.functions: list[dict[str, Any]] = []
        self.constants: list[dict[str, Any]] = []
        self.current_class: str | None = None
        self.all_exports: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition to track methods."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Skip private functions/methods
        if node.name.startswith("_") and node.name not in ("__init__", "__call__"):
            return

        # Extract signature
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Handle return annotation
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        signature = f"{node.name}({', '.join(args)}){returns}"

        # Extract first line of docstring
        docstring = ast.get_docstring(node)
        description = ""
        if docstring:
            # Get first non-empty line
            lines = docstring.strip().split("\n")
            for line in lines:
                line = line.strip()
                if (
                    line
                    and not line.startswith("Args:")
                    and not line.startswith("Returns:")
                ):
                    description = line
                    break

        # Determine if it's a method or function
        kind = "method" if self.current_class else "function"
        full_name = (
            f"{self.current_class}.{node.name}" if self.current_class else node.name
        )

        self.functions.append(
            {
                "name": node.name,
                "full_name": full_name,
                "signature": signature,
                "description": description,
                "module": self.module_path,
                "kind": kind,
                "class_name": self.current_class,
                "lineno": node.lineno,
            }
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        # Convert to FunctionDef for processing
        self.visit_FunctionDef(node)  # type: ignore

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment to capture __all__ and module constants."""
        # Check if this is __all__ assignment
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                # Extract exported names from __all__
                if isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            self.all_exports.add(elt.value)

            # Check if this is a module-level constant (ALL_CAPS)
            elif isinstance(target, ast.Name):
                name = target.id
                # Only capture ALL_CAPS constants at module level (not in classes)
                if (
                    not self.current_class
                    and name.isupper()
                    and not name.startswith("_")
                ):
                    # Try to get a simple value representation
                    value_repr = ast.unparse(node.value) if node.value else "..."

                    self.constants.append(
                        {
                            "name": name,
                            "module": self.module_path,
                            "value": value_repr,
                            "lineno": node.lineno,
                        }
                    )


def scan_python_file(
    file_path: Path, package_root: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Scan a Python file and extract all public functions, methods, and constants.

    Args:
        file_path: Path to Python file
        package_root: Root of the package

    Returns:
        Tuple of (functions, constants) metadata dictionaries
    """
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        # Convert file path to module path
        rel_path = file_path.relative_to(package_root)
        module_parts = list(rel_path.with_suffix("").parts)
        module_path = ".".join(module_parts)

        visitor = FunctionVisitor(module_path)
        visitor.visit(tree)
        return visitor.functions, visitor.constants
    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return [], []


def scan_package(
    package_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Scan entire package and extract all public functions, methods, and constants.

    Args:
        package_path: Path to package root

    Returns:
        Tuple of (all_functions, all_constants) metadata
    """
    all_functions = []
    all_constants = []

    # Find all Python files
    for py_file in package_path.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        functions, constants = scan_python_file(py_file, package_path)
        all_functions.extend(functions)
        all_constants.extend(constants)

    return all_functions, all_constants


def generate_markdown_index(
    functions: list[dict[str, Any]], constants: list[dict[str, Any]]
) -> str:
    """
    Generate markdown index from function and constant metadata.

    Args:
        functions: List of function/method metadata
        constants: List of module constant metadata

    Returns:
        Markdown formatted index
    """
    lines = []

    # Header
    lines.append("# Alphabetical API Index")
    lines.append("")
    lines.append(
        "This is a comprehensive alphabetical index of all public functions, methods, and constants in the biosample-enricher package."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Module Constants Section
    if constants:
        lines.append("## Module Constants")
        lines.append("")
        lines.append(
            "Public constants exported by modules (typically used for configuration, validation, or schema definitions)."
        )
        lines.append("")

        # Group by module
        by_module = defaultdict(list)
        for const in sorted(constants, key=lambda c: c["name"]):
            by_module[const["module"]].append(const)

        for module in sorted(by_module.keys()):
            lines.append(f"### `{module}`")
            lines.append("")

            for const in by_module[module]:
                lines.append(f"#### `{const['name']}`")
                lines.append("")
                # Truncate long values
                value = const["value"]
                if len(value) > 100:
                    value = value[:97] + "..."
                lines.append(f"- **Value**: `{value}`")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Functions and Methods Section
    lines.append("## Functions and Methods")
    lines.append("")

    # Group by first letter
    by_letter = defaultdict(list)
    for func in sorted(functions, key=lambda f: f["full_name"].lower()):
        first_letter = func["full_name"][0].upper()
        by_letter[first_letter].append(func)

    # Generate index
    for letter in sorted(by_letter.keys()):
        lines.append(f"### {letter}")
        lines.append("")

        for func in by_letter[letter]:
            # Function/method name
            lines.append(f"#### `{func['full_name']}`")
            lines.append("")

            # Metadata
            lines.append(f"- **Type**: {func['kind']}")
            lines.append(f"- **Module**: `{func['module']}`")
            if func["class_name"]:
                lines.append(f"- **Class**: `{func['class_name']}`")
            lines.append(f"- **Signature**: `{func['signature']}`")

            # Description
            if func["description"]:
                lines.append(f"- **Description**: {func['description']}")

            lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        "*This index was automatically generated by `scripts/generate_api_index.py`*"
    )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate alphabetical index of all public functions and methods"
    )
    parser.add_argument(
        "--output",
        default="docs/API_INDEX.md",
        help="Output file path (default: docs/API_INDEX.md)",
    )
    args = parser.parse_args()

    # Find package root
    package_path = Path("biosample_enricher")
    if not package_path.exists():
        print(f"❌ Package not found: {package_path}")
        return 1

    print(f"Scanning package: {package_path}")

    # Scan package
    functions, constants = scan_package(package_path)
    print(f"Found {len(functions)} public functions and methods")
    print(f"Found {len(constants)} module constants")

    # Generate markdown
    markdown = generate_markdown_index(functions, constants)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(markdown)

    print(f"✓ Generated index: {output_path}")
    print(f"  Total entries: {len(functions) + len(constants)}")

    # Summary statistics
    methods = sum(1 for f in functions if f["kind"] == "method")
    funcs = sum(1 for f in functions if f["kind"] == "function")
    print(f"  Functions: {funcs}")
    print(f"  Methods: {methods}")
    print(f"  Constants: {len(constants)}")

    return 0


if __name__ == "__main__":
    exit(main())
