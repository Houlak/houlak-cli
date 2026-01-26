"""Constants and configuration for houlak-cli."""

from pathlib import Path

# Application info
APP_NAME = "houlak-cli"
APP_VERSION = "0.1.1"

# AWS Configuration
DEFAULT_REGION = "us-east-1"
DEFAULT_PROFILE = "houlak"
PARAMETER_STORE_PREFIX = "/houlak/cli/databases"
ADMINS_PARAMETER = "/houlak/cli/admins"
DEFAULT_ADMINS = ["eperroud", "gfranco"]

# Local configuration
CONFIG_DIR = Path.home() / f".{APP_NAME}"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_FILE = CONFIG_DIR / "cache.json"

# Default ports by engine
DEFAULT_PORTS = {
    "postgres": 54320,
    "postgresql": 54320,
    "mariadb": 33060,
    "mysql": 33060,
}

# RDS ports by engine
RDS_PORTS = {
    "postgres": 5432,
    "postgresql": 5432,
    "mariadb": 3306,
    "mysql": 3306,
}

# Supported database engines
SUPPORTED_ENGINES = ["postgres", "postgresql", "mariadb", "mysql"]
DEFAULT_ENGINE = "postgres"

# Installation URLs
AWS_CLI_INSTALL_URL = "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
SSM_PLUGIN_INSTALL_URL = "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"

# AWS SSO Configuration
DEFAULT_SSO_START_URL = "https://houlak.awsapps.com/start"
DEFAULT_SSO_REGION = "us-east-1"




