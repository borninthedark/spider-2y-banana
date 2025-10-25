"""Tests for scripts/check-secrets.py secret detection script."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "check_secrets",
    str(Path(__file__).parent.parent / "scripts" / "check-secrets.py"),
)
if spec and spec.loader:
    check_secrets = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_secrets)
else:
    raise ImportError("Failed to load check-secrets module")


class TestRunGitCommand:
    """Test run_git_command helper function."""

    def test_run_git_command_success(self):
        """Test successful git command execution."""
        with patch.object(check_secrets, "run_command") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_run.return_value = mock_result

            result = check_secrets.run_git_command("git status")

            assert result.returncode == 0
            assert result.stdout == "output"
            mock_run.assert_called_once_with(
                "git status", capture_output=True, check=False, shell=True
            )


class TestCheckSensitiveFiles:
    """Test check_sensitive_files function."""

    def test_no_sensitive_files(self):
        """Test when no sensitive files are found."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_sensitive_files()

            assert result is False

    def test_sensitive_files_found(self):
        """Test when sensitive files are detected."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ".env\nsecrets.key"
            mock_git.return_value = mock_result

            result = check_secrets.check_sensitive_files()

            assert result is True


class TestCheckTerraformPasswords:
    """Test check_terraform_passwords function."""

    def test_no_terraform_directory(self):
        """Test when terraform directory doesn't exist."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_exists.return_value = False

            result = check_secrets.check_terraform_passwords()

            assert result is False

    def test_hardcoded_passwords_found(self):
        """Test when hardcoded passwords are detected."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "run_git_command"
        ) as mock_git, patch.object(check_secrets, "print_colored"), patch(
            "builtins.print"
        ):
            mock_exists.return_value = True
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "main.tf:password = 'secret'"
            mock_git.return_value = mock_result

            result = check_secrets.check_terraform_passwords()

            assert result is True

    def test_no_hardcoded_passwords(self):
        """Test when no hardcoded passwords found."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "run_git_command"
        ) as mock_git, patch.object(check_secrets, "print_colored"), patch(
            "builtins.print"
        ):
            mock_exists.return_value = True
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_terraform_passwords()

            assert result is False


class TestCheckAnsiblePasswords:
    """Test check_ansible_passwords function."""

    def test_no_ansible_directory(self):
        """Test when ansible directory doesn't exist."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_exists.return_value = False

            result = check_secrets.check_ansible_passwords()

            assert result is False

    def test_ansible_passwords_found(self):
        """Test when ansible passwords are detected."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "run_git_command"
        ) as mock_git, patch.object(check_secrets, "print_colored"), patch(
            "builtins.print"
        ):
            mock_exists.return_value = True
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "playbook.yml:password: secret"
            mock_git.return_value = mock_result

            result = check_secrets.check_ansible_passwords()

            assert result is True


class TestCheckAwsCredentials:
    """Test check_aws_credentials function."""

    def test_no_aws_credentials(self):
        """Test when no AWS credentials found."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_aws_credentials()

            assert result is False

    def test_aws_credentials_found(self):
        """Test when AWS credentials are detected."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "AKIA" + "TEST" + "EXAMPLE" + "12345"
            mock_git.return_value = mock_result

            result = check_secrets.check_aws_credentials()

            assert result is True


class TestCheckPrivateKeys:
    """Test check_private_keys function."""

    def test_no_private_keys(self):
        """Test when no private keys found."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_private_keys()

            assert result is False

    def test_private_keys_found(self):
        """Test when private keys are detected."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "-----BEGIN PRIVATE KEY-----"
            mock_git.return_value = mock_result

            result = check_secrets.check_private_keys()

            assert result is True


class TestCheckGithubTokens:
    """Test check_github_tokens function."""

    def test_no_github_tokens(self):
        """Test when no GitHub tokens found."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_github_tokens()

            assert result is False

    def test_github_tokens_found(self):
        """Test when GitHub tokens are detected."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "ghp_" + "x" * 36
            mock_git.return_value = mock_result

            result = check_secrets.check_github_tokens()

            assert result is True


class TestCheckSlackTokens:
    """Test check_slack_tokens function."""

    def test_no_slack_tokens(self):
        """Test when no Slack tokens found."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_git.return_value = mock_result

            result = check_secrets.check_slack_tokens()

            assert result is False

    def test_slack_tokens_found(self):
        """Test when Slack tokens are detected."""
        with patch.object(check_secrets, "run_git_command") as mock_git, patch.object(
            check_secrets, "print_colored"
        ), patch("builtins.print"):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "xoxb-" + "0" * 12 + "-" + "0" * 12 + "-" + "x" * 16
            mock_git.return_value = mock_result

            result = check_secrets.check_slack_tokens()

            assert result is True


class TestCheckGitignoreCoverage:
    """Test check_gitignore_coverage function."""

    def test_no_gitignore(self):
        """Test when .gitignore doesn't exist."""
        with patch("os.path.exists") as mock_exists, patch.object(
            check_secrets, "print_colored"
        ):
            mock_exists.return_value = False

            check_secrets.check_gitignore_coverage()

            mock_exists.assert_called_once_with(".gitignore")

    def test_all_patterns_present(self):
        """Test when all required patterns are in .gitignore."""
        with patch("os.path.exists") as mock_exists, patch(
            "builtins.open", create=True
        ) as mock_open, patch.object(check_secrets, "print_colored") as mock_print:
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = (
                "*.env\n*.pem\n*.key\nterraform.tfvars\n.vault_password\n"
                "kubeconfig\nsp-credentials.json"
            )

            check_secrets.check_gitignore_coverage()

            # Should call print_colored with success message
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("All critical patterns" in str(call) for call in calls)

    def test_missing_patterns(self):
        """Test when patterns are missing from .gitignore."""
        with patch("os.path.exists") as mock_exists, patch(
            "builtins.open", create=True
        ) as mock_open, patch.object(check_secrets, "print_colored") as mock_print:
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = "*.env"

            check_secrets.check_gitignore_coverage()

            # Should call print_colored with warning messages
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Warning" in str(call) for call in calls)


class TestMainFunction:
    """Test main function."""

    def test_main_no_errors(self):
        """Test main function when no secrets found."""
        with patch.object(
            check_secrets, "check_sensitive_files", return_value=False
        ), patch.object(
            check_secrets, "check_terraform_passwords", return_value=False
        ), patch.object(
            check_secrets, "check_ansible_passwords", return_value=False
        ), patch.object(
            check_secrets, "check_aws_credentials", return_value=False
        ), patch.object(
            check_secrets, "check_azure_subscription_ids"
        ), patch.object(
            check_secrets, "check_private_keys", return_value=False
        ), patch.object(
            check_secrets, "check_github_tokens", return_value=False
        ), patch.object(
            check_secrets, "check_jwt_tokens"
        ), patch.object(
            check_secrets, "check_slack_tokens", return_value=False
        ), patch.object(
            check_secrets, "check_gitignore_coverage"
        ), patch.object(
            check_secrets, "print_colored"
        ), patch(
            "builtins.print"
        ):
            with pytest.raises(SystemExit) as exc_info:
                check_secrets.main()

            assert exc_info.value.code == 0

    def test_main_with_errors(self):
        """Test main function when secrets are found."""
        with patch.object(
            check_secrets, "check_sensitive_files", return_value=True
        ), patch.object(
            check_secrets, "check_terraform_passwords", return_value=False
        ), patch.object(
            check_secrets, "check_ansible_passwords", return_value=False
        ), patch.object(
            check_secrets, "check_aws_credentials", return_value=False
        ), patch.object(
            check_secrets, "check_azure_subscription_ids"
        ), patch.object(
            check_secrets, "check_private_keys", return_value=False
        ), patch.object(
            check_secrets, "check_github_tokens", return_value=False
        ), patch.object(
            check_secrets, "check_jwt_tokens"
        ), patch.object(
            check_secrets, "check_slack_tokens", return_value=False
        ), patch.object(
            check_secrets, "check_gitignore_coverage"
        ), patch.object(
            check_secrets, "print_colored"
        ), patch(
            "builtins.print"
        ):
            with pytest.raises(SystemExit) as exc_info:
                check_secrets.main()

            assert exc_info.value.code == 1
