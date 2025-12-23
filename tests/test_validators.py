"""Tests for validators module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from houlak_cli.validators import (
    check_aws_cli,
    check_aws_profile,
    check_session_manager_plugin,
    validate_aws_session,
)


class TestCheckAWSCLI:
    """Tests for check_aws_cli function."""
    
    @patch("houlak_cli.validators.shutil.which")
    @patch("houlak_cli.validators.subprocess.run")
    def test_aws_cli_installed(self, mock_run, mock_which):
        """Test when AWS CLI is installed."""
        mock_which.return_value = "/usr/local/bin/aws"
        mock_run.return_value = MagicMock(
            stdout="aws-cli/2.15.0 Python/3.11.0",
            returncode=0
        )
        
        is_installed, version = check_aws_cli()
        
        assert is_installed is True
        assert version == "aws-cli/2.15.0"
    
    @patch("houlak_cli.validators.shutil.which")
    def test_aws_cli_not_installed(self, mock_which):
        """Test when AWS CLI is not installed."""
        mock_which.return_value = None
        
        is_installed, version = check_aws_cli()
        
        assert is_installed is False
        assert version is None


class TestCheckSessionManagerPlugin:
    """Tests for check_session_manager_plugin function."""
    
    @patch("houlak_cli.validators.shutil.which")
    @patch("houlak_cli.validators.subprocess.run")
    def test_plugin_installed(self, mock_run, mock_which):
        """Test when Session Manager Plugin is installed."""
        mock_which.return_value = "/usr/local/bin/session-manager-plugin"
        mock_run.return_value = MagicMock(
            stderr="SessionManagerPlugin 1.2.0.0",
            returncode=0
        )
        
        is_installed, version = check_session_manager_plugin()
        
        assert is_installed is True
    
    @patch("houlak_cli.validators.shutil.which")
    def test_plugin_not_installed(self, mock_which):
        """Test when Session Manager Plugin is not installed."""
        mock_which.return_value = None
        
        is_installed, version = check_session_manager_plugin()
        
        assert is_installed is False


class TestCheckAWSProfile:
    """Tests for check_aws_profile function."""
    
    @patch("houlak_cli.validators.Path")
    def test_profile_exists(self, mock_path):
        """Test when AWS profile exists."""
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_config_file.__truediv__ = lambda self, other: mock_config_file
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "[profile houlak]\nregion = us-east-1"
            mock_path.return_value = mock_config_file
            
            result = check_aws_profile("houlak")
            
            assert result is True
    
    @patch("houlak_cli.validators.Path")
    def test_profile_not_exists(self, mock_path):
        """Test when AWS profile does not exist."""
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_path.return_value = mock_config_file
        
        result = check_aws_profile("houlak")
        
        assert result is False


class TestValidateAWSSession:
    """Tests for validate_aws_session function."""
    
    @patch("houlak_cli.validators.subprocess.run")
    def test_valid_session(self, mock_run):
        """Test when AWS session is valid."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = validate_aws_session("houlak")
        
        assert result is True
    
    @patch("houlak_cli.validators.subprocess.run")
    def test_invalid_session(self, mock_run):
        """Test when AWS session is invalid."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")
        
        result = validate_aws_session("houlak")
        
        assert result is False

