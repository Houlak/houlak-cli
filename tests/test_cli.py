"""Tests for CLI module."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from houlak_cli.cli import app

runner = CliRunner()


class TestCLICommands:
    """Tests for CLI commands."""
    
    @patch("houlak_cli.cli.run_setup_wizard")
    def test_setup_command(self, mock_wizard):
        """Test setup command."""
        result = runner.invoke(app, ["setup"])
        
        assert result.exit_code == 0
        mock_wizard.assert_called_once()
    
    @patch("houlak_cli.cli.connect_to_database")
    def test_db_connect_command(self, mock_connect):
        """Test db-connect command."""
        result = runner.invoke(app, ["db-connect", "--database", "some-db", "--profile", "test-profile"])
        
        # Mock the expected database connection
        mock_connect.assert_called_once_with(database_name="some-db", profile="test-profile", port=None)
        
        # Verify the command executed successfully
        assert result.exit_code == 0
    
    @patch("houlak_cli.cli.list_available_databases")
    def test_list_command(self, mock_list):
        """Test list command."""
        mock_list.return_value = [
            {
                "name": "hk-postgres-dev",
                "project": "hk",
                "engine": "postgres",
                "environment": "dev",
                "region": "us-east-1",
            }
        ]
        
        result = runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        mock_list.assert_called_once()
    
    @patch("houlak_cli.cli.check_all_prerequisites")
    def test_check_command(self, mock_check):
        """Test check command."""
        mock_check.return_value = {
            "aws_cli": True,
            "ssm_plugin": True,
            "aws_profile": True,
            "aws_session": True,
        }
        
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 0
        mock_check.assert_called_once()
    
    @patch("houlak_cli.cli.config")
    def test_config_show_command(self, mock_config):
        """Test config-show command."""
        mock_config.show = MagicMock()
        
        result = runner.invoke(app, ["config-show"])
        
        assert result.exit_code == 0
        mock_config.show.assert_called_once()
    
    @patch("houlak_cli.cli.config")
    def test_config_set_command(self, mock_config):
        """Test config-set command."""
        mock_config.set = MagicMock()
        
        result = runner.invoke(app, ["config-set", "test.key", "test.value"])
        
        assert result.exit_code == 0
        mock_config.set.assert_called_once_with("test.key", "test.value")



