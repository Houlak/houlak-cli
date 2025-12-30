"""Helper functions for AWS profile management."""

import configparser
from pathlib import Path
from typing import List, Optional

from rich.console import Console

console = Console()


def list_aws_profiles() -> List[str]:
    """
    List all AWS profiles configured locally.
    
    Returns:
        List of profile names
    """
    aws_config_file = Path.home() / ".aws" / "config"
    profiles = []
    
    if not aws_config_file.exists():
        return profiles
    
    try:
        config = configparser.ConfigParser()
        config.read(aws_config_file)
        
        for section in config.sections():
            # Sections are either [profile name] or [default]
            if section.startswith("profile "):
                profile_name = section.replace("profile ", "")
                profiles.append(profile_name)
            elif section == "default":
                profiles.append("default")
        
        return sorted(profiles)
    except Exception as e:
        console.print(f"⚠️  Warning: Could not read AWS config: {e}")
        return []


def get_profile_info(profile_name: str) -> Optional[dict]:
    """
    Get information about a specific AWS profile.
    
    Args:
        profile_name: Profile name
        
    Returns:
        Dictionary with profile information or None
    """
    aws_config_file = Path.home() / ".aws" / "config"
    
    if not aws_config_file.exists():
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(aws_config_file)
        
        section_name = f"profile {profile_name}" if profile_name != "default" else "default"
        
        if section_name not in config:
            return None
        
        section = config[section_name]
        info = {
            "name": profile_name,
            "sso_start_url": section.get("sso_start_url"),
            "sso_region": section.get("sso_region"),
            "sso_account_id": section.get("sso_account_id"),
            "sso_role_name": section.get("sso_role_name"),
            "region": section.get("region"),
        }
        
        return info
    except Exception as e:
        console.print(f"⚠️  Warning: Could not read profile info: {e}")
        return None

