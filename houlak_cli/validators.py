"""Validators for prerequisites and configuration."""

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from rich.console import Console
from rich.prompt import Confirm

from houlak_cli.constants import (
    AWS_CLI_INSTALL_URL,
    SSM_PLUGIN_INSTALL_URL,
)

console = Console()


def check_aws_cli() -> Tuple[bool, Optional[str]]:
    """
    Check if AWS CLI is installed.
    
    Returns:
        Tuple of (is_installed, version)
    """
    if not shutil.which("aws"):
        return False, None
    
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip().split()[0]
        return True, version
    except Exception:
        return False, None


def check_session_manager_plugin() -> Tuple[bool, Optional[str]]:
    """
    Check if AWS Session Manager Plugin is installed.
    
    Returns:
        Tuple of (is_installed, version)
    """
    if not shutil.which("session-manager-plugin"):
        return False, None
    
    try:
        result = subprocess.run(
            ["session-manager-plugin"],
            capture_output=True,
            text=True,
        )
        # Plugin returns version info in stderr
        output = result.stderr.strip()
        if "SessionManagerPlugin" in output or "plugin" in output.lower():
            # Extract version if possible
            lines = output.split("\n")
            version = lines[0] if lines else "unknown"
            return True, version
        return False, None
    except Exception:
        return False, None


def check_aws_profile(profile: str) -> bool:
    """
    Check if an AWS profile exists and is configured.
    
    Args:
        profile: AWS profile name
        
    Returns:
        True if profile exists
    """
    aws_config_file = Path.home() / ".aws" / "config"
    
    if not aws_config_file.exists():
        return False
    
    try:
        with open(aws_config_file, "r") as f:
            content = f.read()
            return f"[profile {profile}]" in content or f"[{profile}]" in content
    except Exception:
        return False


def validate_aws_session(profile: str) -> bool:
    """
    Validate that AWS session is active and working.
    
    Args:
        profile: AWS profile name
        
    Returns:
        True if session is valid
    """
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--profile", profile],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def show_aws_cli_installation_guide() -> None:
    """Show AWS CLI installation instructions."""
    console.print("\n📚 [bold]AWS CLI Installation Guide[/bold]\n")
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        console.print("[cyan]macOS:[/cyan]")
        console.print("  brew install awscli")
        console.print("  or")
        console.print("  curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg'")
        console.print("  sudo installer -pkg AWSCLIV2.pkg -target /")
    elif system == "Linux":
        console.print("[cyan]Linux:[/cyan]")
        console.print("  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'")
        console.print("  unzip awscliv2.zip")
        console.print("  sudo ./aws/install")
    elif system == "Windows":
        console.print("[cyan]Windows:[/cyan]")
        console.print("  Download from: https://awscli.amazonaws.com/AWSCLIV2.msi")
    
    console.print(f"\n📖 Full documentation: [link]{AWS_CLI_INSTALL_URL}[/link]")


def show_ssm_plugin_installation_guide() -> None:
    """Show Session Manager Plugin installation instructions."""
    console.print("\n📚 [bold]Session Manager Plugin Installation Guide[/bold]\n")
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        console.print("[cyan]macOS:[/cyan]")
        console.print("  brew install --cask session-manager-plugin")
        console.print("  or")
        console.print("  curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'")
        console.print("  unzip sessionmanager-bundle.zip")
        console.print("  sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin")
    elif system == "Linux":
        console.print("[cyan]Linux:[/cyan]")
        console.print("  curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_64bit/session-manager-plugin.rpm' -o 'session-manager-plugin.rpm'")
        console.print("  sudo yum install -y session-manager-plugin.rpm")
    elif system == "Windows":
        console.print("[cyan]Windows:[/cyan]")
        console.print("  Download from: https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe")
    
    console.print(f"\n📖 Full documentation: [link]{SSM_PLUGIN_INSTALL_URL}[/link]")


def check_all_prerequisites(profile: str = "houlak") -> Dict[str, bool]:
    """
    Check all prerequisites.
    
    Args:
        profile: AWS profile to check
        
    Returns:
        Dictionary with check results
    """
    results = {}
    
    console.print("🔍 [bold]Checking prerequisites...[/bold]\n")
    
    # Check AWS CLI
    aws_installed, aws_version = check_aws_cli()
    results["aws_cli"] = aws_installed
    if aws_installed:
        console.print(f"✅ AWS CLI installed ({aws_version})")
    else:
        console.print("❌ AWS CLI not found")
        if Confirm.ask("Would you like to see installation instructions?"):
            show_aws_cli_installation_guide()
    
    # Check Session Manager Plugin
    ssm_installed, ssm_version = check_session_manager_plugin()
    results["ssm_plugin"] = ssm_installed
    if ssm_installed:
        console.print(f"✅ Session Manager Plugin installed ({ssm_version[:50]}...)")
    else:
        console.print("❌ Session Manager Plugin not found")
        if Confirm.ask("Would you like to see installation instructions?"):
            show_ssm_plugin_installation_guide()
    
    # Check AWS Profile
    profile_exists = check_aws_profile(profile)
    results["aws_profile"] = profile_exists
    if profile_exists:
        console.print(f"✅ AWS Profile '{profile}' configured")
        
        # Check if session is valid
        session_valid = validate_aws_session(profile)
        results["aws_session"] = session_valid
        if session_valid:
            console.print(f"✅ AWS Session is valid")
        else:
            console.print(f"⚠️  AWS Session expired or invalid")
    else:
        console.print(f"❌ AWS Profile '{profile}' not found")
        results["aws_session"] = False
    
    console.print()
    return results


