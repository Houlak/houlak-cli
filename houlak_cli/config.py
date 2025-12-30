"""Configuration management for houlak-cli."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from houlak_cli.constants import CACHE_FILE, CONFIG_DIR, CONFIG_FILE

console = Console()


class Config:
    """Manage houlak-cli configuration."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.cache_file = CACHE_FILE
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.data = self._load_config()
        self.cache = self._load_cache()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"⚠️  Warning: Could not load config: {e}")
            return {}
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"⚠️  Warning: Could not load cache: {e}")
            return {}
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            console.print(f"❌ Error saving config: {e}")
    
    def save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            console.print(f"❌ Error saving cache: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation: 'section.key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation: 'section.key')
            value: Value to set
        """
        keys = key.split(".")
        data = self.data
        
        # Navigate to the nested location
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        
        # Set the value
        data[keys[-1]] = value
        self.save_config()
    
    def get_cached(self, key: str, default: Any = None) -> Any:
        """Get cached value."""
        return self.cache.get(key, default)
    
    def set_cached(self, key: str, value: Any) -> None:
        """Set cached value."""
        self.cache[key] = value
        self.save_cache()
    
    def get_last_connection(self) -> Optional[Dict[str, Any]]:
        """Get last database connection details."""
        return self.cache.get("last_connection")
    
    def save_last_connection(self, database: str, engine: str, env: str, port: int, profile: str) -> None:
        """
        Save last connection details.
        
        Args:
            database: Database name
            engine: Database engine
            env: Environment name
            port: Local port
            profile: AWS profile
        """
        self.cache["last_connection"] = {
            "database": database,
            "engine": engine,
            "environment": env,
            "port": port,
            "profile": profile,
        }
        self.save_cache()
    
    def show(self) -> None:
        """Display current configuration."""
        from rich.table import Table
        
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        def add_rows(data: dict, prefix: str = ""):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    add_rows(value, full_key)
                else:
                    table.add_row(full_key, str(value))
        
        if self.data:
            add_rows(self.data)
        else:
            table.add_row("No configuration", "Run 'houlak-cli setup' first")
        
        console.print(table)


# Global config instance
config = Config()


