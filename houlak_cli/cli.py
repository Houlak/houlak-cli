"""Main CLI interface for houlak-cli using Typer."""

from typing import Optional

import typer
from rich.console import Console

from houlak_cli.aws_helper import list_available_databases
from houlak_cli.config import config
from houlak_cli.db_connect import connect_to_database
from houlak_cli.setup_wizard import run_setup_wizard
from houlak_cli.validators import check_all_prerequisites

app = typer.Typer(
    name="houlak-cli",
    help="Houlak CLI - Database Connection Tool",
    add_completion=False,
)

console = Console()


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


@app.command()
def list(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """List available databases."""
    console.print("\n🔍 [bold]Listing available databases...[/bold]\n")
    
    databases = list_available_databases(profile)
    
    if not databases:
        console.print("⚠️  No databases found in Parameter Store.")
        console.print("\n💡 Tip: Make sure you have:")
        console.print("   - Valid AWS session (run 'aws sso login --profile {profile}')")
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


@app.command()
def check(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """Check prerequisites and configuration."""
    results = check_all_prerequisites(profile)
    
    console.print("\n" + "=" * 60)
    console.print("[bold]Prerequisites Check Summary[/bold]\n")
    
    all_ok = all(results.values())
    
    if all_ok:
        console.print("[bold green]✅ All prerequisites are met![/bold green]")
    else:
        console.print("[bold yellow]⚠️  Some prerequisites are missing[/bold yellow]\n")
        for check_name, status in results.items():
            status_icon = "✅" if status else "❌"
            console.print(f"{status_icon} {check_name.replace('_', ' ').title()}")
    
    console.print("=" * 60 + "\n")


@app.command()
def config_show():
    """Show current configuration."""
    config.show()


@app.command()
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set configuration value."""
    config.set(key, value)
    console.print(f"✅ Configuration '{key}' set to '{value}'")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

