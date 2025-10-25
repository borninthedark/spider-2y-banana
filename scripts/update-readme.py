#!/usr/bin/env python3
"""
Update README.md with dynamically generated table of contents for documentation.

This script scans the docs/ directory for markdown files and updates the
📚 Documentation section in README.md with categorized links.
"""

import re
from pathlib import Path
from typing import Optional


# Documentation categories and their ordering
DOC_CATEGORIES = {
    "Getting Started": [
        "QUICKSTART.md",
        "PROJECT_SUMMARY.md",
        "DEPLOYMENT.md",
    ],
    "CI/CD & Development": [
        "CI_CD_GUIDE.md",
        "WORKFLOW_INTEGRATION_CHECKLIST.md",
        "INTEGRATION_SUMMARY.md",
        "PRECOMMIT_SETUP.md",
        "PYTHON_SCRIPTS_GUIDE.md",
    ],
    "Security & Operations": [
        "security-hardening.md",
        "SECRETS_MANAGEMENT.md",
        "AUDIT_SUMMARY.md",
    ],
    "Advanced Configuration": [
        "JSONNET_INTEGRATION.md",
        "DOMAIN_CONFIGURATION.md",
        "NAMECHEAP_DNS_SETUP.md",
    ],
}

# Application documentation (outside docs/ directory)
APP_DOCS = [
    (
        "osyraa/README.md",
        "Resume App Documentation",
        "Hugo-based resume application details",
    ),
    (
        "osyraa/tests/README.md",
        "Test Suite Documentation",
        "Testing framework and guidelines",
    ),
    (
        "terraform-infrastructure/README.md",
        "Terraform Infrastructure",
        "Infrastructure as code documentation",
    ),
    ("jsonnet/README.md", "Jsonnet Library", "Jsonnet configuration library"),
]


def extract_title(file_path: Path) -> Optional[str]:
    """
    Extract the first heading from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        The first heading text, or None if not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^#\s+(.+)$", line.strip())
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return None


def extract_description(file_path: Path) -> Optional[str]:
    """
    Extract a description from the markdown file.

    Looks for the first paragraph after the title.

    Args:
        file_path: Path to the markdown file

    Returns:
        Description text, or None if not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            found_title = False
            for line in lines:
                # Skip until we find the title
                if not found_title:
                    if re.match(r"^#\s+", line):
                        found_title = True
                    continue

                # Skip empty lines
                if not line.strip():
                    continue

                # Skip other headings
                if re.match(r"^#+\s+", line):
                    continue

                # Found first paragraph
                description = line.strip()
                # Truncate if too long
                if len(description) > 100:
                    description = description[:97] + "..."
                return description
    except Exception:
        pass
    return None


def generate_doc_links() -> str:
    """
    Generate markdown for documentation links.

    Returns:
        Formatted markdown string with categorized documentation links
    """
    docs_dir = Path(__file__).parent.parent / "docs"
    lines = ["## 📚 Documentation", "", "### Project Documentation", ""]

    # Process each category
    for category, files in DOC_CATEGORIES.items():
        lines.append(f"#### {category}")

        for filename in files:
            file_path = docs_dir / filename
            if not file_path.exists():
                print(f"Warning: {filename} not found in docs/")
                continue

            title = extract_title(file_path)
            if not title:
                # Use filename without extension as fallback
                title = filename.replace(".md", "").replace("-", " ").replace("_", " ")

            description = extract_description(file_path)
            if not description:
                description = title

            link = f"docs/{filename}"
            lines.append(f"- **[{title}]({link})** - {description}")

        lines.append("")

    # Add application documentation
    lines.append("#### Application Documentation")
    for path, title, description in APP_DOCS:
        full_path = Path(__file__).parent.parent / path
        if full_path.exists():
            lines.append(f"- **[{title}]({path})** - {description}")

    return "\n".join(lines)


def update_readme() -> bool:
    """
    Update the README.md file with generated documentation links.

    Returns:
        True if successful, False otherwise
    """
    readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}")
        return False

    # Read current README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading README.md: {e}")
        return False

    # Generate new documentation section
    new_docs = generate_doc_links()

    # Find and replace the documentation section
    # Pattern matches from ## 📚 Documentation to ### External Resources
    pattern = r"## 📚 Documentation.*?(?=### External Resources)"

    if not re.search(pattern, content, re.DOTALL):
        print("Error: Could not find documentation section in README.md")
        return False

    # Replace the section
    new_content = re.sub(pattern, new_docs + "\n\n", content, flags=re.DOTALL)

    # Write updated README
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✓ Successfully updated {readme_path}")
        return True
    except Exception as e:
        print(f"Error writing README.md: {e}")
        return False


def main() -> int:
    """Main entry point."""
    success = update_readme()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
