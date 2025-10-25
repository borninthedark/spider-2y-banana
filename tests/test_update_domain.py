"""Tests for scripts/update-domain.py domain update script."""

import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "update_domain",
    str(Path(__file__).parent.parent / "scripts" / "update-domain.py"),
)
if spec and spec.loader:
    update_domain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(update_domain)
else:
    raise ImportError("Failed to load update-domain module")

OLD_DOMAIN = update_domain.OLD_DOMAIN
display_next_steps = update_domain.display_next_steps
get_files_to_update = update_domain.get_files_to_update
print_color = update_domain.print_color
update_file = update_domain.update_file


class TestPrintColor:
    """Test print_color helper function."""

    @patch("builtins.print")
    def test_print_color(self, mock_print):
        """Test colored print output."""
        Colors = update_domain.Colors

        print_color(Colors.GREEN, "Test message")

        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Test message" in args
        assert Colors.GREEN in args


class TestUpdateFile:
    """Test update_file function."""

    def test_update_file_not_exists(self, tmp_path):
        """Test when file doesn't exist."""
        file_path = tmp_path / "nonexistent.txt"

        result = update_file(file_path, "old.com", "new.com")

        assert result is False

    def test_update_file_success(self, tmp_path):
        """Test successful file update."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("domain: old.example.com")

        result = update_file(file_path, "old.example.com", "new.example.com")

        assert result is True
        content = file_path.read_text()
        assert "new.example.com" in content
        assert "old.example.com" not in content

    def test_update_file_multiple_occurrences(self, tmp_path):
        """Test updating multiple occurrences in file."""
        file_path = tmp_path / "config.yaml"
        content = """
        domain: old.com
        api: https://api.old.com
        web: https://www.old.com
        """
        file_path.write_text(content)

        result = update_file(file_path, "old.com", "new.com")

        assert result is True
        new_content = file_path.read_text()
        assert new_content.count("new.com") == 3
        assert "old.com" not in new_content

    def test_update_file_no_matches(self, tmp_path):
        """Test when domain is not in file."""
        file_path = tmp_path / "test.txt"
        original = "domain: different.com"
        file_path.write_text(original)

        result = update_file(file_path, "old.com", "new.com")

        assert result is True
        # File should be unchanged
        assert file_path.read_text() == original


class TestGetFilesToUpdate:
    """Test get_files_to_update function."""

    def test_get_files_to_update(self):
        """Test that function returns list of Path objects."""
        files = get_files_to_update()

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, Path) for f in files)

    def test_files_are_absolute_paths(self):
        """Test that returned paths are absolute."""
        files = get_files_to_update()

        assert all(f.is_absolute() for f in files)


class TestDisplayNextSteps:
    """Test display_next_steps function."""

    def test_display_next_steps(self):
        """Test that next steps are displayed."""
        with patch("builtins.print") as mock_print, patch.object(
            update_domain, "print_color"
        ) as mock_print_color:
            display_next_steps("example.com")

            # Should print header with color
            mock_print_color.assert_called()

            # Should print multiple steps
            assert mock_print.call_count >= 5

            # Check that domain appears in output
            calls_str = " ".join(str(call) for call in mock_print.call_args_list)
            assert "example.com" in calls_str


class TestMainFunction:
    """Test main function."""

    @patch("sys.argv", ["script", "newdomain.com"])
    def test_main_basic(self, tmp_path):
        """Test basic main function execution."""
        with patch.object(
            update_domain, "get_files_to_update"
        ) as mock_get_files, patch.object(
            update_domain, "update_file"
        ) as mock_update, patch.object(
            update_domain, "display_next_steps"
        ) as mock_display, patch.object(
            update_domain, "print_color"
        ), patch(
            "builtins.print"
        ):
            # Mock file list
            test_file = tmp_path / "test.yaml"
            test_file.write_text("content")
            mock_get_files.return_value = [test_file]
            mock_update.return_value = True

            update_domain.main()

            # Verify functions were called
            mock_get_files.assert_called_once()
            mock_update.assert_called()
            mock_display.assert_called_with("newdomain.com")

    @patch("sys.argv", ["script", "newdomain.com", "--old-domain", "custom.old.com"])
    def test_main_with_custom_old_domain(self, tmp_path):
        """Test main with custom old domain."""
        with patch.object(
            update_domain, "get_files_to_update"
        ) as mock_get_files, patch.object(
            update_domain, "update_file"
        ) as mock_update, patch.object(
            update_domain, "display_next_steps"
        ), patch.object(
            update_domain, "print_color"
        ), patch(
            "builtins.print"
        ):
            test_file = tmp_path / "test.yaml"
            test_file.write_text("content")
            mock_get_files.return_value = [test_file]
            mock_update.return_value = True

            update_domain.main()

            # Verify update was called with custom old domain
            assert mock_update.called
            call_args = mock_update.call_args[0]
            assert call_args[1] == "custom.old.com"
            assert call_args[2] == "newdomain.com"

    @patch("sys.argv", ["script", "example.com"])
    def test_main_counts_updated_files(self, tmp_path):
        """Test that main correctly counts updated files."""
        with patch.object(
            update_domain, "get_files_to_update"
        ) as mock_get_files, patch.object(
            update_domain, "update_file"
        ) as mock_update, patch.object(
            update_domain, "display_next_steps"
        ), patch.object(
            update_domain, "print_color"
        ), patch(
            "builtins.print"
        ):
            # Create multiple test files
            files = []
            for i in range(3):
                f = tmp_path / f"test{i}.yaml"
                f.write_text("content")
                files.append(f)

            mock_get_files.return_value = files
            mock_update.return_value = True

            update_domain.main()

            # Verify all files were attempted to update
            assert mock_update.call_count == 3

    @patch("sys.argv", ["script", "example.com"])
    def test_main_handles_missing_files(self, tmp_path):
        """Test main handles missing files gracefully."""
        with patch.object(
            update_domain, "get_files_to_update"
        ) as mock_get_files, patch.object(update_domain, "update_file") as mock_update:
            # Mock file that doesn't exist
            missing_file = tmp_path / "missing.yaml"
            mock_get_files.return_value = [missing_file]
            mock_update.return_value = False

            # Should not raise exception
            update_domain.main()

            mock_update.assert_called_once()


class TestOldDomainConstant:
    """Test OLD_DOMAIN constant."""

    def test_old_domain_defined(self):
        """Test that OLD_DOMAIN is defined."""
        assert OLD_DOMAIN is not None
        assert isinstance(OLD_DOMAIN, str)
        assert len(OLD_DOMAIN) > 0

    def test_old_domain_format(self):
        """Test that OLD_DOMAIN looks like a domain."""
        # Should contain at least one dot
        assert "." in OLD_DOMAIN
        # Should not have spaces
        assert " " not in OLD_DOMAIN
