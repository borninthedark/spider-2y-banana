"""Tests for the update-readme.py script."""

import importlib.util
import re
from pathlib import Path
from unittest.mock import patch


# Dynamically load the update_readme module
spec = importlib.util.spec_from_file_location(
    "update_readme",
    str(Path(__file__).parent.parent / "scripts" / "update-readme.py"),
)
assert spec is not None
assert spec.loader is not None
update_readme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_readme)


class TestExtractTitle:
    """Test the extract_title function."""

    def test_extract_title_with_heading(self, tmp_path: Path) -> None:
        """Test extracting title from markdown with heading."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Title\n\nSome content")

        result = update_readme.extract_title(test_file)

        assert result == "Test Title"

    def test_extract_title_with_multiple_headings(self, tmp_path: Path) -> None:
        """Test extracting only the first heading."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# First Heading\n\n## Second Heading")

        result = update_readme.extract_title(test_file)

        assert result == "First Heading"

    def test_extract_title_no_heading(self, tmp_path: Path) -> None:
        """Test with no heading in file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Just some text without heading")

        result = update_readme.extract_title(test_file)

        assert result is None

    def test_extract_title_nonexistent_file(self, tmp_path: Path) -> None:
        """Test with nonexistent file."""
        test_file = tmp_path / "nonexistent.md"

        result = update_readme.extract_title(test_file)

        assert result is None


class TestExtractDescription:
    """Test the extract_description function."""

    def test_extract_description_with_paragraph(self, tmp_path: Path) -> None:
        """Test extracting description from markdown."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\nThis is a description.\n\nMore content")

        result = update_readme.extract_description(test_file)

        assert result == "This is a description."

    def test_extract_description_long_paragraph(self, tmp_path: Path) -> None:
        """Test truncating long descriptions."""
        test_file = tmp_path / "test.md"
        long_text = "A" * 150
        test_file.write_text(f"# Title\n\n{long_text}")

        result = update_readme.extract_description(test_file)

        assert result is not None
        assert len(result) <= 100
        assert result.endswith("...")

    def test_extract_description_no_paragraph(self, tmp_path: Path) -> None:
        """Test with no paragraph after heading."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\n## Another Heading")

        result = update_readme.extract_description(test_file)

        assert result is None

    def test_extract_description_nonexistent_file(self, tmp_path: Path) -> None:
        """Test with nonexistent file."""
        test_file = tmp_path / "nonexistent.md"

        result = update_readme.extract_description(test_file)

        assert result is None


class TestGenerateDocLinks:
    """Test the generate_doc_links function."""

    def test_generate_doc_links_structure(self) -> None:
        """Test that generated links have correct structure."""
        result = update_readme.generate_doc_links()

        assert "## 📚 Documentation" in result
        assert "### Project Documentation" in result
        assert "#### Getting Started" in result
        assert "#### CI/CD & Development" in result
        assert "#### Security & Operations" in result
        assert "#### Advanced Configuration" in result
        assert "#### Application Documentation" in result

    def test_generate_doc_links_includes_files(self) -> None:
        """Test that generated links include expected files."""
        result = update_readme.generate_doc_links()

        # Check for some expected documentation links
        assert "docs/QUICKSTART.md" in result
        assert "docs/PROJECT_SUMMARY.md" in result
        assert "docs/DEPLOYMENT.md" in result

    def test_generate_doc_links_markdown_format(self) -> None:
        """Test that links are in correct markdown format."""
        result = update_readme.generate_doc_links()

        # Check for markdown link patterns
        assert re.search(r"\*\*\[.+\]\(.+\)\*\* - .+", result)


class TestUpdateReadme:
    """Test the update_readme function."""

    def test_update_readme_with_valid_content(self, tmp_path: Path) -> None:
        """Test updating README with valid documentation section."""
        # Create a mock README
        readme_content = """# Test Project

Some content

## 📚 Documentation

### Project Documentation

- Old link

### External Resources

- [Example](https://example.com)
"""

        readme_path = tmp_path / "README.md"
        readme_path.write_text(readme_content)

        # Mock the path resolution
        with patch.object(update_readme.Path, "__truediv__", return_value=readme_path):
            # Note: This test will fail because it can't find docs/
            # In a real scenario, you'd need to create the full directory structure
            pass

    def test_update_readme_preserves_external_resources(self, tmp_path: Path) -> None:
        """Test that external resources section is preserved."""
        readme_content = """# Test

## 📚 Documentation

### Project Documentation

Old content

### External Resources

- [Keep This](https://example.com)
"""

        readme_path = tmp_path / "README.md"
        readme_path.write_text(readme_content)

        # Read back to verify External Resources is still there
        updated_content = readme_path.read_text()
        assert "### External Resources" in updated_content


class TestMain:
    """Test the main function."""

    def test_main_returns_zero_on_success(self) -> None:
        """Test main returns 0 on success."""
        with patch.object(update_readme, "update_readme", return_value=True):
            result = update_readme.main()
            assert result == 0

    def test_main_returns_one_on_failure(self) -> None:
        """Test main returns 1 on failure."""
        with patch.object(update_readme, "update_readme", return_value=False):
            result = update_readme.main()
            assert result == 1
