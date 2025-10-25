#!/usr/bin/env python3
"""DRY (Don't Repeat Yourself) enforcement tool.

Detects code duplication and outputs remediation tasks.
"""

import argparse
import ast
import difflib
import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils import Colors, get_project_root, print_colored, print_error, print_info


class CodeBlock:
    """Represents a block of code for duplication detection."""

    def __init__(self, file_path: Path, start_line: int, end_line: int, content: str):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.hash = hashlib.md5(content.encode()).hexdigest()

    def __repr__(self):
        return (
            f"{self.file_path}:{self.start_line}-{self.end_line} "
            f"({self.end_line - self.start_line + 1} lines)"
        )


class DuplicationDetector:
    """Detects code duplication in Python files."""

    def __init__(self, min_lines: int = 5, similarity_threshold: float = 0.8):
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold
        self.blocks: List[CodeBlock] = []
        self.duplicates: List[Tuple[CodeBlock, CodeBlock, float]] = []

    def extract_functions(self, file_path: Path) -> List[CodeBlock]:
        """Extract function definitions from a Python file."""
        blocks = []
        try:
            with open(file_path, "r") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    if end_line - start_line + 1 >= self.min_lines:
                        func_content = "\n".join(
                            content.splitlines()[start_line - 1 : end_line]
                        )
                        blocks.append(
                            CodeBlock(file_path, start_line, end_line, func_content)
                        )
        except SyntaxError:
            print_error(f"Syntax error in {file_path}, skipping")
        except Exception as e:
            print_error(f"Error processing {file_path}: {e}")

        return blocks

    def extract_code_blocks(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks from a file using sliding window."""
        blocks: List[CodeBlock] = []
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # Skip if file is too small
            if len(lines) < self.min_lines:
                return blocks

            # Extract blocks using sliding window
            for i in range(len(lines) - self.min_lines + 1):
                for window_size in range(self.min_lines, min(50, len(lines) - i + 1)):
                    content = "".join(lines[i : i + window_size])
                    # Skip blocks that are mostly whitespace or comments
                    stripped = content.strip()
                    if len(stripped) < 20:
                        continue
                    if stripped.count("#") / len(stripped.splitlines()) > 0.5:
                        continue

                    blocks.append(
                        CodeBlock(file_path, i + 1, i + window_size, content.strip())
                    )
        except Exception as e:
            print_error(f"Error reading {file_path}: {e}")

        return blocks

    def calculate_similarity(self, block1: CodeBlock, block2: CodeBlock) -> float:
        """Calculate similarity between two code blocks."""
        # Normalize whitespace for comparison
        content1 = " ".join(block1.content.split())
        content2 = " ".join(block2.content.split())

        # Use sequence matcher for similarity
        matcher = difflib.SequenceMatcher(None, content1, content2)
        return matcher.ratio()

    def find_duplicates(self, files: List[Path], use_functions: bool = False):
        """Find duplicate code across files."""
        print_info(f"Analyzing {len(files)} Python files...")

        # Extract code blocks
        for file_path in files:
            if use_functions:
                blocks = self.extract_functions(file_path)
            else:
                blocks = self.extract_code_blocks(file_path)
            self.blocks.extend(blocks)

        print_info(f"Found {len(self.blocks)} code blocks to analyze")

        # Group by hash for exact matches
        hash_groups: Dict[str, List[CodeBlock]] = defaultdict(list)
        for block in self.blocks:
            hash_groups[block.hash].append(block)

        # Find exact duplicates
        for hash_val, blocks in hash_groups.items():
            if len(blocks) > 1:
                # Add all pairs of duplicates
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        self.duplicates.append((blocks[i], blocks[j], 1.0))

        # Find similar blocks (not exact)
        seen_pairs: Set[Tuple[str, str]] = set()
        for i, block1 in enumerate(self.blocks):
            if i % 100 == 0 and i > 0:
                print_info(f"Progress: {i}/{len(self.blocks)} blocks analyzed")

            for block2 in self.blocks[i + 1 :]:
                # Skip if same file and overlapping lines
                if block1.file_path == block2.file_path and not (
                    block1.end_line < block2.start_line
                    or block2.end_line < block1.start_line
                ):
                    continue

                # Skip if already found as exact duplicate
                pair_key = (
                    f"{block1.file_path}:{block1.start_line}",
                    f"{block2.file_path}:{block2.start_line}",
                )
                if pair_key in seen_pairs:
                    continue

                similarity = self.calculate_similarity(block1, block2)
                if similarity >= self.similarity_threshold and similarity < 1.0:
                    self.duplicates.append((block1, block2, similarity))
                    seen_pairs.add(pair_key)

    def print_report(self):
        """Print duplication report."""
        if not self.duplicates:
            print_colored("\n✓ No significant code duplication found!", Colors.GREEN)
            return

        print_colored(
            f"\n✗ Found {len(self.duplicates)} duplicate code blocks",
            Colors.RED,
        )

        # Sort by similarity (highest first)
        sorted_dupes = sorted(self.duplicates, key=lambda x: x[2], reverse=True)

        print("\n" + "=" * 80)
        print("DUPLICATION REPORT")
        print("=" * 80)

        for idx, (block1, block2, similarity) in enumerate(sorted_dupes, 1):
            print(f"\n{idx}. Similarity: {similarity:.1%}")
            print(f"   Location 1: {block1}")
            print(f"   Location 2: {block2}")

            if similarity == 1.0:
                print(f"   {Colors.RED}EXACT DUPLICATE{Colors.NC}")
            else:
                print(
                    f"   {Colors.YELLOW}SIMILAR CODE " f"({similarity:.1%}){Colors.NC}"
                )

        print("\n" + "=" * 80)
        print("REMEDIATION TASKS")
        print("=" * 80)

        # Group by file for remediation tasks
        file_groups: Dict[Path, List[Tuple]] = defaultdict(list)
        for block1, block2, similarity in sorted_dupes:
            file_groups[block1.file_path].append((block1, block2, similarity))

        for file_path, duplicates in file_groups.items():
            print(f"\n{Colors.CYAN}{file_path}{Colors.NC}")
            for block1, block2, similarity in duplicates:
                if similarity == 1.0:
                    print(
                        f"  [ ] Extract duplicate code at lines "
                        f"{block1.start_line}-{block1.end_line} to shared function"
                    )
                    print(f"      Also found in: {block2.file_path}")
                else:
                    print(
                        f"  [ ] Review similar code at lines "
                        f"{block1.start_line}-{block1.end_line}"
                    )
                    print(
                        f"      Similar to: {block2.file_path}:"
                        f"{block2.start_line}-{block2.end_line}"
                    )


def find_python_files(
    root: Path, exclude_dirs: Optional[Set[str]] = None
) -> List[Path]:
    """Find all Python files in the project."""
    if exclude_dirs is None:
        exclude_dirs = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
        }

    python_files = []
    for path in root.rglob("*.py"):
        # Skip if in excluded directory
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        python_files.append(path)

    return python_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Detect code duplication in Python files"
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=5,
        help="Minimum lines for a code block (default: 5)",
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.8,
        help="Similarity threshold 0-1 (default: 0.8)",
    )
    parser.add_argument(
        "--functions-only",
        action="store_true",
        help="Only analyze function definitions",
    )
    parser.add_argument(
        "--path", type=str, help="Path to analyze (default: project root)"
    )

    args = parser.parse_args()

    # Get project root or specified path
    if args.path:
        root = Path(args.path).resolve()
    else:
        root = get_project_root()

    print_colored("DRY (Don't Repeat Yourself) Enforcement Tool", Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    print(f"Analyzing: {root}")
    print(f"Min lines: {args.min_lines}")
    print(f"Similarity threshold: {args.similarity:.0%}")
    print(f"Mode: {'Functions only' if args.functions_only else 'All code blocks'}")
    print()

    # Find Python files
    files = find_python_files(root)
    if not files:
        print_error("No Python files found!")
        sys.exit(1)

    # Detect duplicates
    detector = DuplicationDetector(
        min_lines=args.min_lines, similarity_threshold=args.similarity
    )
    detector.find_duplicates(files, use_functions=args.functions_only)

    # Print report
    detector.print_report()

    # Exit with error if duplicates found
    if detector.duplicates:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
