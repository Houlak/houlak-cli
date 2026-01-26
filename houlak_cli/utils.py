"""Utility functions for houlak-cli."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


def run_command(
    command: List[str],
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """
    Run a shell command.
    
    Args:
        command: Command and arguments as list
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        timeout: Command timeout in seconds
        
    Returns:
        CompletedProcess instance
    """
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout,
        )
        return result
    except subprocess.TimeoutExpired:
        console.print(f"❌ Command timed out after {timeout} seconds")
        raise
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Command failed with exit code {e.returncode}")
        if e.stderr:
            console.print(f"Error: {e.stderr}")
        raise


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON as dictionary
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        console.print(f"⚠️  Warning: Could not parse {file_path}: {e}")
        return {}


def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """
    Save dictionary as JSON file.
    
    Args:
        file_path: Path to save JSON file
        data: Dictionary to save
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def is_port_in_use(port: int) -> bool:
    """
    Check if a local port is in use.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is in use, False otherwise
    """
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(start_port: int, max_attempts: int = 10) -> Optional[int]:
    """
    Find an available port starting from a given port.
    
    Args:
        start_port: Starting port number
        max_attempts: Maximum number of ports to try
        
    Returns:
        Available port number or None if not found
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None




