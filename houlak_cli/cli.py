"""Main CLI interface for houlak-cli using Typer."""

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from houlak_cli.admin import add_database_to_parameter_store, require_admin
from houlak_cli.aws_helper import list_available_databases
from houlak_cli.config import config  # This imports the Config instance
from houlak_cli.constants import APP_VERSION
from houlak_cli.db_connect import connect_to_database
from houlak_cli.profile_helper import list_aws_profiles
from houlak_cli.setup_wizard import run_setup_wizard

app = typer.Typer(
    name="houlak-cli",
    help="Houlak CLI - Comprehensive AWS toolkit for developers",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version information.",
    ),
):
    """Main callback - shows welcome message if no command provided."""
    # Handle version flag first - this works even when a command is provided
    if version:
        console.print(f"houlak-cli version {APP_VERSION}")
        raise typer.Exit()
    
    # Show welcome message if no command was provided
    if ctx.invoked_subcommand is None:
        welcome_message = Panel.fit(
            "[bold cyan]🚀 Welcome to Houlak CLI![/bold cyan]\n\n"
            "A comprehensive toolkit for developers to interact with AWS services.\n\n"
            "[yellow]AWS Profile Configuration Commands:[/yellow]\n"
            "  • [cyan]config-aws-profile[/cyan] - Configure AWS CLI profile for houlak-cli\n"
            "  • [cyan]config-list[/cyan] - List all AWS profiles configured locally\n"
            "\n"
            "[dim]Note: If you already have AWS profiles configured via 'aws configure',\n"
            "you can use them directly with the --profile flag (e.g., --profile my-profile)[/dim]\n\n"
            "[yellow]Database Commands:[/yellow]\n"
            "  • [cyan]db-connect[/cyan] - Connect to a database using its name from Parameter Store\n"
            "  • [cyan]db-list[/cyan] - List available databases\n\n"
            "[yellow]Admin Commands:[/yellow]\n"
            "  • [cyan]admin-db-add[/cyan] - Add database configuration to Parameter Store (admin only)\n\n"
            "[dim]Run 'houlak-cli --help' or 'houlak-cli -h' for more information[/dim]\n"
            f"[dim]Version {APP_VERSION}[/dim]",
            title="[bold]Houlak CLI[/bold]",
            border_style="cyan",
        )
        console.print(welcome_message)
        sys.exit(0)


@app.command(name="db-list")
def db_list(
    profile: Optional[str] = typer.Option(None, "--profile", help="AWS profile (or set AWS_PROFILE/AWS_DEFAULT_PROFILE env var)"),
):
    """List databases available for connection using the db-connect command.
    
    AWS Profile can be specified via:
      • --profile flag
      • AWS_PROFILE environment variable
      • AWS_DEFAULT_PROFILE environment variable
    """
    # Resolve profile from --profile flag or environment variables
    resolved_profile = profile or os.environ.get('AWS_PROFILE') or os.environ.get('AWS_DEFAULT_PROFILE')
    
    if not resolved_profile:
        console.print("❌ [bold red]AWS profile not specified[/bold red]\n")
        console.print("Please specify a profile using one of these methods:")
        console.print("  • Use --profile flag: [cyan]houlak-cli db-list --profile <profile-name>[/cyan]")
        console.print("  • Set AWS_PROFILE: [cyan]export AWS_PROFILE=<profile-name>[/cyan]")
        console.print("  • Set AWS_DEFAULT_PROFILE: [cyan]export AWS_DEFAULT_PROFILE=<profile-name>[/cyan]")
        console.print("\n💡 List available profiles: [cyan]houlak-cli config-list[/cyan]")
        sys.exit(1)
    
    console.print("\n🔍 [bold]Listing available databases...[/bold]\n")
    
    databases = list_available_databases(resolved_profile)
    
    if not databases:
        console.print("⚠️  No databases found in Parameter Store.")
        console.print("\n💡 Tip: Make sure you have:")
        console.print(f"   - Valid AWS session (run 'aws sso login --profile {profile}')")
        console.print("   - Access to Parameter Store")
        return
    
    from rich.table import Table
    
    table = Table(title="Available Databases")
    table.add_column("Name", style="cyan")
    table.add_column("Project", style="green")
    table.add_column("Engine", style="yellow")
    table.add_column("Environment", style="magenta")
    table.add_column("Region", style="blue")
    
    for db in databases:
        table.add_row(
            db.get("name", "N/A"),
            db.get("project", "N/A"),
            db.get("engine", "N/A"),
            db.get("environment", "N/A"),
            db.get("region", "N/A"),
        )
    
    console.print(table)
    console.print(f"\n💡 Connect to a database: [cyan]houlak-cli db-connect <engine> --env <env>[/cyan]")

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def db_connect(
    ctx: typer.Context,
    database_name: str = typer.Option(..., "--database", "-d", help="Database name from Parameter Store"),
    profile: Optional[str] = typer.Option(None, "--profile", help="AWS profile to use (or set AWS_PROFILE/AWS_DEFAULT_PROFILE env var)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Local port (optional, uses default based on engine)"),
):
    """Connect to database through Session Manager via bastion host.
    
    AWS Profile can be specified via:
      • --profile flag
      • AWS_PROFILE environment variable
      • AWS_DEFAULT_PROFILE environment variable
      • AWS_PROFILE=my-profile as additional argument
    
    If none is provided, an error will be shown.
    """
    # Parse additional arguments for AWS_PROFILE assignments to handle inline ENV syntax
    if ctx.args:
        # Update environment variables if inline arguments contain AWS_PROFILE or AWS_DEFAULT_PROFILE
        inline_env_vars = {
            kv.split('=', 1)[0].strip(): kv.split('=', 1)[1].strip()
            for kv in ctx.args if '=' in kv
            if kv.split('=', 1)[0].strip() in ['AWS_PROFILE', 'AWS_DEFAULT_PROFILE']
        }
        os.environ.update(inline_env_vars)

    # Resolve AWS profile with a consistent precedence order: --profile > inline > env vars
    resolved_profile = profile or inline_env_vars.get('AWS_PROFILE') or os.environ.get('AWS_PROFILE') or os.environ.get('AWS_DEFAULT_PROFILE')

    if not resolved_profile:
        console.print("❌ [bold red]AWS profile not specified[/bold red]\n")
        console.print("Please specify a profile using one of these methods:")
        console.print("  • Use --profile flag: [cyan]houlak-cli db-connect -d <db-name> --profile <profile-name>[/cyan]")
        console.print("  • Set AWS_PROFILE: [cyan]export AWS_PROFILE=<profile-name>[/cyan]")
        console.print("  • Set AWS_DEFAULT_PROFILE: [cyan]export AWS_DEFAULT_PROFILE=<profile-name>[/cyan]")
        console.print("  • Pass as argument: [cyan]houlak-cli db-connect -d <db-name> AWS_PROFILE=<profile-name>[/cyan]")
        console.print("\n💡 List available profiles: [cyan]houlak-cli config-list[/cyan]")
        sys.exit(1)
    if not resolved_profile:
        console.print("❌ [bold red]AWS profile not specified[/bold red]\n")
        console.print("Please specify a profile using one of these methods:")
        console.print("  • Use --profile flag: [cyan]houlak-cli db-connect -d <db-name> --profile <profile-name>[/cyan]")
        console.print("  • Set AWS_PROFILE: [cyan]export AWS_PROFILE=<profile-name>[/cyan]")
        console.print("  • Set AWS_DEFAULT_PROFILE: [cyan]export AWS_DEFAULT_PROFILE=<profile-name>[/cyan]")
        console.print("  • Pass as argument: [cyan]houlak-cli db-connect -d <db-name> AWS_PROFILE=<profile-name>[/cyan]")
        console.print("\n💡 List available profiles: [cyan]houlak-cli config-list[/cyan]")
        sys.exit(1)
    
    connect_to_database(
        database_name=database_name,
        profile=resolved_profile,
        port=port,
    )


@app.command(name="config-aws-profile", help="Configure an AWS CLI profile for the tool (use it only if needed).")
def config_aws_profile():
    """Configure AWS CLI profile for use with houlak-cli.

    This command helps you set up an AWS CLI profile that houlak-cli will use.
    If you already have AWS profiles configured (via 'aws configure sso' or 'aws configure'),
    you can skip this command and use your existing profiles directly with the --profile flag.

    [dim]Hint: Use this command only if you need to configure your AWS profile.[/dim]
    """
    run_setup_wizard()





@app.command(name="config-list")
def config_list():
    """List all AWS profiles configured locally in ~/.aws/config."""
    console.print("\n🔍 [bold]AWS Profiles Configured Locally[/bold]\n")
    
    profiles = list_aws_profiles()
    
    if not profiles:
        console.print("⚠️  No AWS profiles found.")
        console.print("\n💡 Tip: Configure an AWS profile first:")
        console.print("   - Run 'houlak-cli setup' to configure a profile")
        console.print("   - Or manually edit ~/.aws/config")
        return
    
    from rich.table import Table
    
    table = Table(title="AWS Profiles")
    table.add_column("Profile Name", style="cyan")
    table.add_column("SSO Start URL", style="green")
    table.add_column("Account ID", style="yellow")
    table.add_column("Role Name", style="magenta")
    table.add_column("Region", style="blue")
    
    from houlak_cli.profile_helper import get_profile_info
    
    for profile_name in profiles:
        info = get_profile_info(profile_name)
        if info:
            table.add_row(
                profile_name,
                info.get("sso_start_url", "N/A"),
                info.get("sso_account_id", "N/A"),
                info.get("sso_role_name", "N/A"),
                info.get("region", "N/A"),
            )
        else:
            table.add_row(profile_name, "N/A", "N/A", "N/A", "N/A")
    
    console.print(table)
    console.print(f"\n💡 Use a profile: [cyan]houlak-cli db-connect --profile <profile-name> --env <env>[/cyan]")


# Comentado temporalmente
# @app.command()
# def check(
#     profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
# ):
#     """Check prerequisites and configuration."""
#     results = check_all_prerequisites(profile)
#     
#     console.print("\n" + "=" * 60)
#     console.print("[bold]Prerequisites Check Summary[/bold]\n")
#     
#     all_ok = all(results.values())
#     
#     if all_ok:
#         console.print("[bold green]✅ All prerequisites are met![/bold green]")
#     else:
#         console.print("[bold yellow]⚠️  Some prerequisites are missing[/bold yellow]\n")
#         for check_name, status in results.items():
#             status_icon = "✅" if status else "❌"
#             console.print(f"{status_icon} {check_name.replace('_', ' ').title()}")
#     
#     console.print("=" * 60 + "\n")

# Admin commands
@app.command(name="admin-db-add")
def admin_db_add(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile to use for storing configuration"),
):
    """Add a database configuration to Parameter Store (admin only)."""
    from houlak_cli.admin import prompt_for_database_config

    # Check admin privileges first
    if not require_admin(profile):
        sys.exit(1)

    # Interactive database configuration
    db_config = prompt_for_database_config()
    
    console.print(f"\n➕ [bold]Adding database '{db_config['name']}' to Parameter Store[/bold]\n")

    if add_database_to_parameter_store(db_config['name'], db_config, profile):
        console.print(f"\n✅ Database '{db_config['name']}' successfully added!")
        console.print(f"\n💡 Developers can now connect using: [cyan]houlak-cli db-connect --database {db_config['name']} --profile <their-profile>[/cyan]")
    else:
        console.print(f"\n❌ Failed to add database '{db_config['name']}'")
        sys.exit(1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
