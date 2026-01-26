"""Admin functions for houlak-cli."""

import json
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console

from houlak_cli.aws_helper import get_aws_session
from houlak_cli.constants import ADMINS_PARAMETER, DEFAULT_ADMINS, DEFAULT_PROFILE, DEFAULT_REGION

console = Console()


def get_current_aws_user(profile: str = DEFAULT_PROFILE) -> Optional[str]:
    """
    Get current AWS user/identity from STS.
    
    Args:
        profile: AWS profile name
        
    Returns:
        Username or None if error
    """
    try:
        session = get_aws_session(profile)
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        
        # Extract username from ARN
        # ARN format: arn:aws:sts::account:assumed-role/role-name/session-name
        # or: arn:aws:iam::account:user/username
        arn = identity.get("Arn", "")
        
        if ":user/" in arn:
            # IAM user
            return arn.split(":user/")[-1]
        elif ":assumed-role/" in arn:
            # Assumed role - extract session name (usually contains username)
            session_part = arn.split("/")[-1]
            # Session name format might be: username@account or just username
            if "@" in session_part:
                return session_part.split("@")[0]
            return session_part
        else:
            # Fallback: use the last part of ARN
            return arn.split("/")[-1] if "/" in arn else arn.split(":")[-1]
            
    except Exception as e:
        console.print(f"⚠️  Warning: Could not get AWS user identity: {e}")
        return None


def get_admin_users(profile: str = DEFAULT_PROFILE) -> List[str]:
    """
    Get list of admin users from Parameter Store.
    
    Args:
        profile: AWS profile name
        
    Returns:
        List of admin usernames
    """
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        try:
            response = ssm.get_parameter(
                Name=ADMINS_PARAMETER,
                WithDecryption=True
            )
            admins = json.loads(response["Parameter"]["Value"])
            return admins.get("users", DEFAULT_ADMINS)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                # Parameter doesn't exist, try to initialize with defaults
                # But don't fail if we can't (might not have permissions)
                try:
                    initialize_admin_users(profile)
                except Exception:
                    pass  # Silently fail, will use defaults
                return DEFAULT_ADMINS
            raise
            
    except Exception as e:
        console.print(f"⚠️  Warning: Could not get admin users: {e}")
        return DEFAULT_ADMINS


def initialize_admin_users(profile: str = DEFAULT_PROFILE) -> bool:
    """
    Initialize admin users parameter in Parameter Store.
    
    Args:
        profile: AWS profile name
        
    Returns:
        True if successful
    """
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        admins_data = {
            "users": DEFAULT_ADMINS
        }
        
        ssm.put_parameter(
            Name=ADMINS_PARAMETER,
            Value=json.dumps(admins_data),
            Type="String",
            Description="Houlak CLI admin users",
            Overwrite=False,  # Don't overwrite if exists
        )
        
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterAlreadyExists":
            # Already exists, that's fine
            return True
        console.print(f"❌ Error initializing admin users: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Error initializing admin users: {e}")
        return False


def is_admin_user(username: Optional[str], profile: str = DEFAULT_PROFILE) -> bool:
    """
    Check if a user is an admin.
    
    Args:
        username: Username to check (None to check current user)
        profile: AWS profile name
        
    Returns:
        True if user is admin
    """
    if username is None:
        username = get_current_aws_user(profile)
        if username is None:
            return False
    
    admins = get_admin_users(profile)
    return username.lower() in [admin.lower() for admin in admins]


def require_admin(profile: str = DEFAULT_PROFILE) -> bool:
    """
    Require admin access. Check current user and exit if not admin.
    
    Args:
        profile: AWS profile name
        
    Returns:
        True if user is admin, exits otherwise
    """
    current_user = get_current_aws_user(profile)
    
    if current_user is None:
        console.print("❌ Could not determine current AWS user")
        return False
    
    if not is_admin_user(current_user, profile):
        console.print(f"\n❌ [bold red]Access Denied[/bold red]")
        console.print(f"User '{current_user}' is not authorized to use admin commands.")
        console.print(f"\n💡 Contact an admin to get access.")
        return False
    
    return True

from rich.prompt import Prompt

def prompt_for_database_config():
    """
    Prompt user interactively for database configuration details.
    Returns database_config_dict with database name included.
    """
    console.print("\n[bold cyan]🔧 Database Configuration Setup[/bold cyan]\n")
    console.print("[dim]Please provide the following information to add a new database to Parameter Store.[/dim]\n")

    database_name = Prompt.ask("Database name (e.g., hk-postgres-dev)").strip()
    project = Prompt.ask("Project name").strip()
    engine = Prompt.ask("Database engine", choices=["postgres", "mariadb"], default="postgres")
    environment = Prompt.ask("Environment", choices=["dev", "qa", "prod"])
    bastion_instance_id = Prompt.ask("Bastion EC2 instance ID (e.g., i-1234567890abcdef0)").strip()
    rds_endpoint = Prompt.ask("RDS endpoint").strip()
    rds_port = int(Prompt.ask("RDS port", default="5432"))
    region = Prompt.ask("AWS region", default=DEFAULT_REGION).strip()

    db_config = {
        "name": database_name,
        "project": project,
        "engine": engine,
        "environment": environment,
        "bastionInstanceId": bastion_instance_id,
        "rdsEndpoint": rds_endpoint,
        "rdsPort": rds_port,
        "region": region,
    }

    return db_config


def add_database_to_parameter_store(
    database_name: str,
    config: dict,
    profile: str = DEFAULT_PROFILE,
) -> bool:
    """
    Add or update a database configuration in Parameter Store.
    
    Args:
        database_name: Database name (e.g., 'hk-postgres-dev')
        config: Database configuration dictionary
        profile: AWS profile name
        
    Returns:
        True if successful
    """
    from houlak_cli.constants import PARAMETER_STORE_PREFIX
    
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        parameter_name = f"{PARAMETER_STORE_PREFIX}/{database_name}"
        
        # Validate required fields
        required_fields = ["project", "engine", "environment", "bastionInstanceId", "rdsEndpoint", "rdsPort"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            console.print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        ssm.put_parameter(
            Name=parameter_name,
            Value=json.dumps(config, indent=2),
            Type="String",
            Description=f"Database configuration for {database_name}",
            Overwrite=True,
        )
        
        console.print(f"✅ Database '{database_name}' added/updated in Parameter Store")
        return True
        
    except ClientError as e:
        console.print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Error adding database: {e}")
        return False

