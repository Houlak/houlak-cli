"""Tests for config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from houlak_cli.config import Config


class TestConfig:
    """Tests for Config class."""
    
    def test_get_set_simple_key(self):
        """Test getting and setting simple configuration keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            config = Config()
            config.config_dir = config_dir
            config.config_file = config_file
            config.data = {}
            
            config.set("test_key", "test_value")
            assert config.get("test_key") == "test_value"
    
    def test_get_set_nested_key(self):
        """Test getting and setting nested configuration keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            config = Config()
            config.config_dir = config_dir
            config.config_file = config_file
            config.data = {}
            
            config.set("section.subsection.key", "value")
            assert config.get("section.subsection.key") == "value"
            assert config.get("section.subsection") == {"key": "value"}
    
    def test_get_default_value(self):
        """Test getting default value when key doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            config = Config()
            config.config_dir = config_dir
            config.config_file = config_file
            config.data = {}
            
            assert config.get("nonexistent_key", "default") == "default"
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            config1 = Config()
            config1.config_dir = config_dir
            config1.config_file = config_file
            config1.data = {}
            config1.set("test_key", "test_value")
            config1.save_config()
            
            config2 = Config()
            config2.config_dir = config_dir
            config2.config_file = config_file
            config2.data = config2._load_config()
            
            assert config2.get("test_key") == "test_value"
    
    def test_cache_operations(self):
        """Test cache get and set operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            cache_file = config_dir / "cache.json"
            
            config = Config()
            config.config_dir = config_dir
            config.cache_file = cache_file
            config.cache = {}
            
            config.set_cached("test_key", "test_value")
            assert config.get_cached("test_key") == "test_value"
    
    def test_save_last_connection(self):
        """Test saving last connection details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            cache_file = config_dir / "cache.json"
            
            config = Config()
            config.config_dir = config_dir
            config.cache_file = cache_file
            config.cache = {}
            
            config.save_last_connection(
                database="hk-postgres-dev",
                engine="postgres",
                env="dev",
                port=54320,
                profile="houlak",
            )
            
            last_conn = config.get_last_connection()
            assert last_conn is not None
            assert last_conn["database"] == "hk-postgres-dev"
            assert last_conn["engine"] == "postgres"
            assert last_conn["environment"] == "dev"
            assert last_conn["port"] == 54320
            assert last_conn["profile"] == "houlak"

