"""AWS helper functions for Session Manager and Parameter Store."""

import json
import subprocess
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console

from houlak_cli.constants import DEFAULT_PROFILE, DEFAULT_REGION, PARAMETER_STORE_PREFIX

console = Console()


def get_aws_session(profile: str = DEFAULT_PROFILE, region: str = DEFAULT_REGION) -> boto3.Session:
    """
    Get AWS session with profile.
    
    Args:
        profile: AWS profile name
        region: AWS region
        
    Returns:
        Boto3 Session
    """
    try:
        return boto3.Session(profile_name=profile, region_name=region)
    except Exception as e:
        console.print(f"❌ Error creating AWS session: {e}")
        raise


def execute_sso_login(profile: str) -> bool:
    """
    Execute AWS SSO login.
    
    Args:
        profile: AWS profile name
        
    Returns:
        True if successful
    """
    try:
        console.print(f"🔐 Executing AWS SSO login for profile '{profile}'...")
        result = subprocess.run(
            ["aws", "sso", "login", "--profile", profile],
            check=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        console.print(f"❌ SSO login failed")
        return False
    except Exception as e:
        console.print(f"❌ Error during SSO login: {e}")
        return False


def get_database_config(database_name: str, profile: str = DEFAULT_PROFILE) -> Optional[Dict]:
    """
    Get database configuration from Parameter Store.
    
    Args:
        database_name: Database name (e.g., 'hk-postgres-dev')
        profile: AWS profile
        
    Returns:
        Database configuration dictionary or None
    """
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        parameter_name = f"{PARAMETER_STORE_PREFIX}/{database_name}"
        
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        config = json.loads(response["Parameter"]["Value"])
        return config
        
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            console.print(f"❌ Database '{database_name}' not found in Parameter Store")
        else:
            console.print(f"❌ AWS Error: {e}")
        return None
    except NoCredentialsError:
        console.print("❌ No AWS credentials found. Please configure AWS CLI.")
        return None
    except json.JSONDecodeError:
        console.print(f"❌ Invalid JSON in parameter '{database_name}'")
        return None
    except Exception as e:
        console.print(f"❌ Error fetching database config: {e}")
        return None


def list_available_databases(profile: str = DEFAULT_PROFILE) -> List[Dict]:
    """
    List all available databases from Parameter Store.
    
    Args:
        profile: AWS profile
        
    Returns:
        List of database configurations
    """
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        # Get all parameters under the prefix
        response = ssm.get_parameters_by_path(
            Path=PARAMETER_STORE_PREFIX,
            Recursive=True,
            WithDecryption=True
        )
        
        databases = []
        for param in response.get("Parameters", []):
            try:
                config = json.loads(param["Value"])
                # Extract database name from parameter name
                db_name = param["Name"].replace(f"{PARAMETER_STORE_PREFIX}/", "")
                config["name"] = db_name
                databases.append(config)
            except json.JSONDecodeError:
                console.print(f"⚠️  Warning: Invalid JSON in parameter {param['Name']}")
                continue
        
        return databases
        
    except NoCredentialsError:
        console.print("❌ No AWS credentials found. Please configure AWS CLI.")
        return []
    except Exception as e:
        console.print(f"❌ Error listing databases: {e}")
        return []


def start_ssm_port_forwarding(
    instance_id: str,
    remote_host: str,
    remote_port: int,
    local_port: int,
    profile: str = DEFAULT_PROFILE,
    region: str = DEFAULT_REGION,
) -> subprocess.Popen:
    """
    Start SSM port forwarding session.
    
    Args:
        instance_id: EC2 instance ID (bastion host)
        remote_host: Remote host to forward to (RDS endpoint)
        remote_port: Remote port (RDS port)
        local_port: Local port to listen on
        profile: AWS profile
        region: AWS region
        
    Returns:
        Subprocess Popen object
    """
    parameters = json.dumps({
        "host": [remote_host],
        "portNumber": [str(remote_port)],
        "localPortNumber": [str(local_port)]
    })
    
    command = [
        "aws", "ssm", "start-session",
        "--target", instance_id,
        "--document-name", "AWS-StartPortForwardingSessionToRemoteHost",
        "--parameters", parameters,
        "--profile", profile,
        "--region", region
    ]
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return process
    except Exception as e:
        console.print(f"❌ Error starting port forwarding: {e}")
        raise


def check_parameter_store_access(profile: str = DEFAULT_PROFILE) -> bool:
    """
    Check if we have access to Parameter Store.
    
    Args:
        profile: AWS profile
        
    Returns:
        True if access is available
    """
    try:
        session = get_aws_session(profile)
        ssm = session.client("ssm")
        
        # Try to list parameters
        ssm.get_parameters_by_path(
            Path=PARAMETER_STORE_PREFIX,
            MaxResults=1
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            console.print("❌ Access denied to Parameter Store. Check IAM permissions.")
        return False
    except Exception:
        return False




