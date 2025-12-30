"""Main CLI interface for houlak-cli using Typer."""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from houlak_cli.admin import add_database_to_parameter_store, require_admin
from houlak_cli.aws_helper import list_available_databases
from houlak_cli.config import config
from houlak_cli.constants import APP_VERSION
from houlak_cli.db_connect import connect_to_database
from houlak_cli.profile_helper import list_aws_profiles
from houlak_cli.setup_wizard import run_setup_wizard

app = typer.Typer(
    name="houlak-cli",
    help="Houlak CLI - Comprehensive AWS toolkit for developers",
    add_completion=False,
    invoke_without_command=True,
)

console = Console()


# Add version callback
def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print(f"houlak-cli version {APP_VERSION}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version information",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Main callback - shows welcome message if no command provided."""
    if ctx.invoked_subcommand is None:
        welcome_message = Panel.fit(
            "[bold cyan]🚀 Welcome to Houlak CLI![/bold cyan]\n\n"
            "A comprehensive toolkit for developers to interact with AWS services.\n\n"
            "[yellow]Available commands:[/yellow]\n"
            "  • [cyan]setup[/cyan] - Configure houlak-cli\n"
            "  • [cyan]db-connect[/cyan] - Connect to a database\n"
            "  • [cyan]db-list[/cyan] - List available databases\n"
            "  • [cyan]config-current[/cyan] - Show current configuration\n"
            "  • [cyan]config-list[/cyan] - List AWS profiles\n"
            "  • [cyan]admin-db-add[/cyan] - Add database to Parameter Store (admin only)\n\n"
            "[dim]Run 'houlak-cli --help' for more information[/dim]\n"
            f"[dim]Version {APP_VERSION}[/dim]",
            title="[bold]Houlak CLI[/bold]",
            border_style="cyan",
        )
        console.print(welcome_message)
        sys.exit(0)


@app.command()
def setup():
    """Run setup wizard to configure houlak-cli."""
    run_setup_wizard()


@app.command()
def db_connect(
    engine: str = typer.Argument("postgres", help="Database engine (postgres/mariadb)"),
    env: str = typer.Option(..., "--env", "-e", help="Environment (dev/qa/prod)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Local port"),
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
    project: Optional[str] = typer.Option(None, "--project", help="Project name"),
):
    """Connect to database through Session Manager."""
    connect_to_database(
        engine=engine,
        env=env,
        port=port,
        profile=profile,
        project=project,
    )


@app.command(name="db-list")
def db_list(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """List available databases."""
    console.print("\n🔍 [bold]Listing available databases...[/bold]\n")
    
    databases = list_available_databases(profile)
    
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


@app.command(name="config-current")
def config_current():
    """Show current houlak-cli configuration."""
    config.show()


@app.command(name="config-list")
def config_list():
    """List all AWS profiles configured locally."""
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


# Admin commands
@app.command(name="admin-db-add")
def admin_db_add(
    database_name: str = typer.Argument(..., help="Database name (e.g., hk-postgres-dev)"),
    project: str = typer.Option(..., "--project", help="Project name"),
    engine: str = typer.Option(..., "--engine", help="Database engine (postgres/mariadb)"),
    environment: str = typer.Option(..., "--env", help="Environment (dev/qa/prod)"),
    bastion_instance_id: str = typer.Option(..., "--bastion", help="Bastion EC2 instance ID"),
    rds_endpoint: str = typer.Option(..., "--rds-endpoint", help="RDS endpoint"),
    rds_port: int = typer.Option(..., "--rds-port", help="RDS port"),
    region: str = typer.Option("us-east-1", "--region", help="AWS region"),
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """Add a database configuration to Parameter Store (admin only)."""
    if not require_admin(profile):
        sys.exit(1)
    
    console.print(f"\n➕ [bold]Adding database '{database_name}' to Parameter Store[/bold]\n")
    
    db_config = {
        "project": project,
        "engine": engine,
        "environment": environment,
        "bastionInstanceId": bastion_instance_id,
        "rdsEndpoint": rds_endpoint,
        "rdsPort": rds_port,
        "region": region,
    }
    
    if add_database_to_parameter_store(database_name, db_config, profile):
        console.print(f"\n✅ Database '{database_name}' successfully added!")
    else:
        console.print(f"\n❌ Failed to add database '{database_name}'")
        sys.exit(1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
