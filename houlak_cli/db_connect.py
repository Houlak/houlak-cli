"""Database connection module for houlak-cli."""

import signal
import sys
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

from houlak_cli.aws_helper import (
    execute_sso_login,
    get_database_config,
    start_ssm_port_forwarding,
)
from houlak_cli.config import config
from houlak_cli.constants import DEFAULT_ENGINE, DEFAULT_PORTS, RDS_PORTS
from houlak_cli.utils import find_available_port, is_port_in_use
from houlak_cli.validators import validate_aws_session

console = Console()


def build_database_name(project: str, engine: str, env: str) -> str:
    """
    Build database name from components.
    
    Format: {project}-{engine}-{env}
    Examples: hk-postgres-dev, hk-mariadb-dev, creditel-postgres-dev
    
    Args:
        project: Project name
        engine: Database engine
        env: Environment name
        
    Returns:
        Database name
    """
    # Normalize engine name
    engine_normalized = engine.lower()
    if engine_normalized == "postgresql":
        engine_normalized = "postgres"
    
    return f"{project}-{engine_normalized}-{env}"


def connect_to_database(
    engine: str = DEFAULT_ENGINE,
    env: str = None,
    port: Optional[int] = None,
    profile: str = "houlak",
    project: Optional[str] = None,
) -> None:
    """
    Connect to database through Session Manager.
    
    Args:
        engine: Database engine (postgres/mariadb)
        env: Environment (dev/qa/prod)
        port: Local port (optional)
        profile: AWS profile
        project: Project name (optional, will be prompted if not provided)
    """
    if not env:
        console.print("❌ Environment (--env) is required")
        sys.exit(1)
    
    # Get project name if not provided
    if not project:
        project = Prompt.ask("[cyan]Enter project name[/cyan]", default="").strip()
        if not project:
            console.print("❌ Project name is required")
            sys.exit(1)
    
    # Build database name
    database_name = build_database_name(project, engine, env)
    
    console.print(f"\n🔍 Looking for database: [cyan]{database_name}[/cyan]\n")
    
    # Validate AWS session
    if not validate_aws_session(profile):
        console.print(f"⚠️  AWS session expired or invalid for profile '{profile}'")
        if Confirm.ask("Run SSO login?", default=True):
            if not execute_sso_login(profile):
                console.print("❌ SSO login failed")
                sys.exit(1)
        else:
            console.print("❌ Cannot proceed without valid AWS session")
            sys.exit(1)
    
    # Get database configuration from Parameter Store
    db_config = get_database_config(database_name, profile)
    
    if not db_config:
        console.print(f"❌ Database '{database_name}' not found in Parameter Store")
        console.print("\n💡 Tip: Use 'houlak-cli list' to see available databases")
        sys.exit(1)
    
    # Extract configuration values
    bastion_instance_id = db_config.get("bastionInstanceId")
    rds_endpoint = db_config.get("rdsEndpoint")
    rds_port = db_config.get("rdsPort")
    region = db_config.get("region", "us-east-1")
    
    if not bastion_instance_id or not rds_endpoint or not rds_port:
        console.print("❌ Invalid database configuration. Missing required fields.")
        sys.exit(1)
    
    # Determine local port
    if not port:
        # Try default port for engine
        default_port = DEFAULT_PORTS.get(engine.lower(), DEFAULT_PORTS[DEFAULT_ENGINE])
        port = default_port
        
        # Check if port is available
        if is_port_in_use(port):
            console.print(f"⚠️  Port {port} is already in use")
            available_port = find_available_port(port)
            if available_port:
                if Confirm.ask(f"Use port {available_port} instead?", default=True):
                    port = available_port
                else:
                    console.print("❌ Connection cancelled")
                    sys.exit(1)
            else:
                console.print("❌ No available ports found")
                sys.exit(1)
    else:
        # Check if specified port is available
        if is_port_in_use(port):
            console.print(f"⚠️  Port {port} is already in use")
            available_port = find_available_port(port)
            if available_port:
                if Confirm.ask(f"Use port {available_port} instead?", default=True):
                    port = available_port
                else:
                    console.print("❌ Connection cancelled")
                    sys.exit(1)
            else:
                console.print("❌ No available ports found")
                sys.exit(1)
    
    # Start port forwarding
    console.print(f"\n🚀 Starting port forwarding...\n")
    console.print(f"   Instance: {bastion_instance_id}")
    console.print(f"   Remote: {rds_endpoint}:{rds_port}")
    console.print(f"   Local: localhost:{port}\n")
    
    try:
        process = start_ssm_port_forwarding(
            instance_id=bastion_instance_id,
            remote_host=rds_endpoint,
            remote_port=rds_port,
            local_port=port,
            profile=profile,
            region=region,
        )
        
        # Wait a moment for connection to establish
        import time
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process has terminated, read error
            stdout, stderr = process.communicate()
            console.print("❌ Port forwarding failed")
            if stderr:
                console.print(f"Error: {stderr}")
            sys.exit(1)
        
        # Save connection info
        config.save_last_connection(
            database=database_name,
            engine=engine,
            env=env,
            port=port,
            profile=profile,
        )
        
        # Show connection info (BASIC format)
        console.print("=" * 60)
        console.print(f"[bold green]✅ Connected to {database_name}![/bold green]\n")
        console.print("Database connection details:")
        console.print(f"  Host: [cyan]localhost[/cyan]")
        console.print(f"  Port: [cyan]{port}[/cyan]\n")
        console.print("[yellow]Press Ctrl+C to stop the tunnel.[/yellow]")
        console.print("=" * 60 + "\n")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            console.print("\n\n🛑 Stopping tunnel...")
            process.terminate()
            process.wait()
            console.print("✅ Tunnel stopped")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep tunnel open (block until Ctrl+C)
        try:
            process.wait()
        except KeyboardInterrupt:
            signal_handler(None, None)
        
    except Exception as e:
        console.print(f"❌ Error starting port forwarding: {e}")
        sys.exit(1)

