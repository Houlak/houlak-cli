"""Database connection module for houlak-cli."""

import os
import signal
import subprocess
import sys
import threading
import time
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

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
    database_name: str,
    profile: str = "houlak",
    port: Optional[int] = None,
) -> None:
    """
    Connect to database through Session Manager.
    
    Args:
        database_name: Database name from Parameter Store
        profile: AWS profile
        port: Local port (optional)
    """
    console.print(f"\n🔍 Looking for database: [cyan]{database_name}[/cyan]")
    console.print(f"📋 Using AWS profile: [cyan]{profile}[/cyan]\n")
    
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
        console.print("\n💡 Tip: Use 'houlak-cli db-list' to see available databases")
        sys.exit(1)
    
    # Extract configuration values
    bastion_instance_id = db_config.get("bastionInstanceId")
    rds_endpoint = db_config.get("rdsEndpoint")
    rds_port = db_config.get("rdsPort")
    region = db_config.get("region", "us-east-1")
    engine = db_config.get("engine", "postgres")
    environment = db_config.get("environment", "unknown")
    
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
            console.print("❌ [bold red]Port forwarding failed to start[/bold red]\n")
            
            # Show detailed error information
            console.print("[red]═══════════════ Error Details ═══════════════[/red]")
            if stderr and stderr.strip():
                console.print(f"[yellow]Error Output:[/yellow]")
                console.print(f"[dim]{stderr.strip()}[/dim]")
            if stdout and stdout.strip():
                console.print(f"\n[yellow]Standard Output:[/yellow]")
                console.print(f"[dim]{stdout.strip()}[/dim]")
            console.print("[red]════════════════════════════════════════════[/red]\n")
            
            # Provide helpful guidance based on error code and content
            console.print("[yellow]Common causes:[/yellow]")
            error_code = process.returncode
            
            if error_code == 255 or "255" in str(stderr):
                console.print("  • AWS SSO session expired or invalid")
                console.print("  • Insufficient permissions to connect to the bastion host")
                console.print("  • Bastion host is not running or unreachable")
                console.print("  • Network connectivity issues with AWS Session Manager")
            elif "TargetNotConnected" in str(stderr):
                console.print("  • Bastion host is not connected to SSM")
                console.print("  • SSM Agent may not be running on the bastion host")
            elif "AccessDenied" in str(stderr):
                console.print("  • IAM permissions issue - check your role/user permissions")
                console.print("  • Missing ssm:StartSession permission")
            else:
                console.print("  • Network connectivity issues")
                console.print("  • SSM Session Manager plugin not installed or outdated")
                console.print("  • Invalid database configuration")
                console.print(f"  • Unexpected error code: {error_code}")
            
            console.print("\n💡 [bold]Troubleshooting steps:[/bold]")
            console.print(f"  1. Refresh AWS credentials: [cyan]aws sso login --profile {profile}[/cyan]")
            console.print(f"  2. Verify AWS identity: [cyan]aws sts get-caller-identity --profile {profile}[/cyan]")
            console.print(f"  3. Check bastion instance status: [cyan]aws ec2 describe-instances --instance-ids {bastion_instance_id} --profile {profile}[/cyan]")
            console.print(f"  4. Test SSM connectivity: [cyan]aws ssm describe-instance-information --profile {profile}[/cyan]")
            console.print("  5. Verify Session Manager plugin: [cyan]session-manager-plugin[/cyan]")
            console.print(f"  6. Check region setting (currently: {region})")
            console.print("\n")
            
            sys.exit(1)
        
        # Save connection info
        config.save_last_connection(
            database=database_name,
            engine=engine,
            env=environment,
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
        shutdown_event = threading.Event()
        
        def signal_handler(sig, frame):
            if shutdown_event.is_set():
                # Already shutting down, force exit
                console.print("\n🛑 Force exiting...")
                os._exit(1)
            
            shutdown_event.set()
            console.print("\n\n🛑 Stopping tunnel...")
            
            try:
                # Try graceful termination first
                process.terminate()
                
                # Wait up to 3 seconds for graceful termination
                for i in range(30):  # 30 * 0.1 = 3 seconds
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                
                # If still running, force kill
                if process.poll() is None:
                    console.print("⚠️  Force terminating...")
                    process.kill()
                    process.wait(timeout=1)
                
                console.print("✅ Tunnel stopped")
                
            except (subprocess.TimeoutExpired, OSError, ProcessLookupError):
                # Process already terminated or killed
                console.print("✅ Tunnel stopped")
            except Exception as e:
                console.print(f"⚠️  Error stopping tunnel: {e}")
            finally:
                sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep tunnel open (block until Ctrl+C or process ends)
        try:
            # Wait for process to finish naturally
            return_code = process.wait()
            if return_code != 0:
                console.print(f"\n⚠️  [bold yellow]Tunnel process ended unexpectedly with code {return_code}[/bold yellow]\n")
                
                # Try to get any remaining output
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stderr and stderr.strip():
                        console.print("[red]═══════════════ Error Details ═══════════════[/red]")
                        console.print(f"[dim]{stderr.strip()}[/dim]")
                        console.print("[red]════════════════════════════════════════════[/red]\n")
                except:
                    pass
                
                # Provide specific guidance for code 255
                if return_code == 255:
                    console.print("[yellow]Code 255 typically indicates:[/yellow]")
                    console.print("  • AWS SSO session expired during the connection")
                    console.print("  • Bastion host connection lost or became unavailable")
                    console.print("  • Network connectivity interrupted")
                    console.print("  • SSM Session Manager connection timeout")
                    console.print("\n💡 [bold]Recommended actions:[/bold]")
                    console.print(f"  1. Refresh credentials: [cyan]aws sso login --profile {profile}[/cyan]")
                    console.print("  2. Check bastion host is still running in AWS Console")
                    console.print("  3. Verify network connectivity to AWS")
                    console.print("  4. Try reconnecting: [cyan]houlak-cli db-connect -d {database_name} --profile {profile}[/cyan]")
                else:
                    console.print(f"[yellow]Connection ended with error code {return_code}[/yellow]")
                    console.print("\n💡 Check AWS Session Manager logs for more details")
            else:
                console.print("\n✅ Tunnel ended naturally")
            
        except KeyboardInterrupt:
            signal_handler(None, None)
        except Exception as e:
            console.print(f"\n❌ Unexpected error: {e}")
            signal_handler(None, None)
        
    except Exception as e:
        console.print(f"❌ Error starting port forwarding: {e}")
        sys.exit(1)

