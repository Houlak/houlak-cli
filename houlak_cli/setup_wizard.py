"""Advanced setup wizard for houlak-cli configuration."""

import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

from houlak_cli.aws_helper import check_parameter_store_access, execute_sso_login, list_available_databases
from houlak_cli.config import config
from houlak_cli.constants import (
    DEFAULT_PROFILE,
    DEFAULT_REGION,
    DEFAULT_SSO_REGION,
    DEFAULT_SSO_START_URL,
)
from houlak_cli.validators import check_aws_profile, validate_aws_session

console = Console()


def write_aws_profile(
    profile_name: str,
    sso_start_url: str,
    sso_region: str,
    account_id: str,
    role_name: str,
    region: str,
) -> bool:
    """
    Write AWS profile configuration to ~/.aws/config.
    
    Args:
        profile_name: Profile name
        sso_start_url: SSO start URL
        sso_region: SSO region
        account_id: AWS account ID
        role_name: SSO role name
        region: Default region
        
    Returns:
        True if successful
    """
    aws_config_dir = Path.home() / ".aws"
    aws_config_file = aws_config_dir / "config"
    
    # Ensure .aws directory exists
    aws_config_dir.mkdir(parents=True, exist_ok=True)
    
    # Read existing config if it exists
    existing_content = ""
    if aws_config_file.exists():
        with open(aws_config_file, "r") as f:
            existing_content = f.read()
    
    # Check if profile already exists
    profile_section = f"[profile {profile_name}]"
    if profile_section in existing_content or f"[{profile_name}]" in existing_content:
        if not Confirm.ask(f"Profile '{profile_name}' already exists. Overwrite?"):
            return False
        
        # Remove existing profile section
        lines = existing_content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if line.strip() == profile_section or line.strip() == f"[{profile_name}]":
                skip = True
                continue
            if skip and line.strip().startswith("[") and not line.strip().startswith(f"[profile {profile_name}]"):
                skip = False
            if not skip:
                new_lines.append(line)
        existing_content = "\n".join(new_lines)
    
    # Build profile configuration
    profile_config = f"""
{profile_section}
sso_start_url = {sso_start_url}
sso_region = {sso_region}
sso_account_id = {account_id}
sso_role_name = {role_name}
region = {region}
"""
    
    # Append to config file
    try:
        with open(aws_config_file, "a") as f:
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            f.write(profile_config.strip() + "\n")
        
        console.print(f"✅ AWS profile '{profile_name}' configured successfully!")
        return True
    except Exception as e:
        console.print(f"❌ Error writing AWS config: {e}")
        return False


def run_setup_wizard() -> None:
    """Run the interactive setup wizard."""
    console.print("\n🚀 [bold]Houlak CLI Setup Wizard[/bold]\n")
    console.print("This wizard will help you configure houlak-cli for first-time use.\n")
    console.print("[yellow]ℹ️  Important:[/yellow] houlak-cli is based on AWS profiles configured locally.")
    console.print("This wizard will help you create an AWS profile in ~/.aws/config.\n")
    
    # Step 1: AWS Profile Configuration
    console.print("[bold cyan]Step 1: AWS Profile Configuration[/bold cyan]\n")
    
    profile_name = Prompt.ask(
        "AWS Profile Name",
        default=DEFAULT_PROFILE,
    )
    
    sso_start_url = Prompt.ask(
        "SSO Start URL",
        default=DEFAULT_SSO_START_URL,
    )
    
    sso_region = Prompt.ask(
        "SSO Region",
        default=DEFAULT_SSO_REGION,
    )
    
    account_id = Prompt.ask(
        "AWS Account ID",
    )
    
    role_name = Prompt.ask(
        "SSO Role Name",
    )
    
    region = Prompt.ask(
        "Default Region",
        default=DEFAULT_REGION,
    )
    
    console.print()
    
    # Write AWS profile
    if not write_aws_profile(
        profile_name=profile_name,
        sso_start_url=sso_start_url,
        sso_region=sso_region,
        account_id=account_id,
        role_name=role_name,
        region=region,
    ):
        console.print("❌ Setup failed. Please try again.")
        return
    
    # Step 2: SSO Login
    console.print("\n[bold cyan]Step 2: AWS SSO Login[/bold cyan]\n")
    console.print("You need to log in to AWS SSO to continue.\n")
    
    if not Confirm.ask("Proceed with SSO login now?"):
        console.print("⚠️  You can run 'aws sso login --profile {profile_name}' manually later.")
    else:
        if execute_sso_login(profile_name):
            console.print("✅ SSO login successful!")
        else:
            console.print("❌ SSO login failed. Please try again manually.")
            return
    
    # Step 3: Test Parameter Store Access
    console.print("\n[bold cyan]Step 3: Testing Parameter Store Access[/bold cyan]\n")
    
    if check_parameter_store_access(profile_name):
        console.print("✅ Parameter Store access verified!")
    else:
        console.print("❌ Cannot access Parameter Store. Please check IAM permissions.")
        if not Confirm.ask("Continue anyway?"):
            return
    
    # Step 4: List Available Databases
    console.print("\n[bold cyan]Step 4: Listing Available Databases[/bold cyan]\n")
    
    databases = list_available_databases(profile_name)
    
    if databases:
        from rich.table import Table
        
        table = Table(title="Available Databases")
        table.add_column("Name", style="cyan")
        table.add_column("Project", style="green")
        table.add_column("Engine", style="yellow")
        table.add_column("Environment", style="magenta")
        
        for db in databases:
            table.add_row(
                db.get("name", "N/A"),
                db.get("project", "N/A"),
                db.get("engine", "N/A"),
                db.get("environment", "N/A"),
            )
        
        console.print(table)
    else:
        console.print("⚠️  No databases found in Parameter Store.")
    
    # Step 5: Save Configuration
    console.print("\n[bold cyan]Step 5: Saving Configuration[/bold cyan]\n")
    
    config.set("aws.profile", profile_name)
    config.set("aws.region", region)
    config.set("aws.sso_start_url", sso_start_url)
    config.set("aws.sso_region", sso_region)
    config.set("aws.account_id", account_id)
    config.set("aws.role_name", role_name)
    
    console.print("✅ Configuration saved successfully!")
    
    # Final summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]✅ Setup Complete![/bold green]\n")
    console.print(f"AWS Profile: {profile_name}")
    console.print(f"Region: {region}")
    console.print(f"Databases Found: {len(databases)}")
    console.print("\nYou can now use houlak-cli to connect to databases.")
    console.print("Try: [cyan]houlak-cli db-list[/cyan] to see available databases.")
    console.print("=" * 60 + "\n")



