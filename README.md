# Houlak CLI

A comprehensive command-line tool suite for developers to interact with AWS services.

## Overview

`houlak-cli` is a developer-friendly toolkit that provides multiple tools for interacting with AWS services. The tool abstracts the complexity of AWS operations, allowing developers to focus on their work without needing to understand AWS internals.

Currently, `houlak-cli` includes:

- **Database connections**: Connect to RDS databases through AWS Session Manager with a simple command

More tools and commands will be added in the future to expand the capabilities of the CLI.

## Prerequisites

Before using `houlak-cli`, you need:

- **Python 3.8+**
- **AWS CLI v2** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS Session Manager Plugin** - [Installation Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
- **AWS Profile Configuration** - `houlak-cli` is based on AWS profiles configured locally in `~/.aws/config`. The first step is to have your AWS profile configured for the account you want to connect to. You can configure it manually or use the `setup` command.

## Installation

### First-time Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/Houlak/houlak-cli.git
```

Or clone and install in development mode:

```bash
git clone https://github.com/Houlak/houlak-cli.git
cd houlak-cli
pip install -e .
```

### Updating to Latest Version

If you already have `houlak-cli` installed, update it with:

```bash
pip install --upgrade git+https://github.com/Houlak/houlak-cli.git
```

Or if installed in development mode:

```bash
cd houlak-cli
git pull origin main
pip install -e .
```

### Check Current Version

Check which version you have installed:

```bash
houlak-cli --version
```

## Quick Start

### 1. Initial Setup

**Important**: `houlak-cli` is based on AWS profiles configured locally in `~/.aws/config`. The first step is to have your AWS profile configured for the account you want to connect to.

Run the setup wizard to configure your AWS profile:

```bash
houlak-cli setup
```

The wizard will guide you through:

- Checking prerequisites (AWS CLI, Session Manager Plugin)
- Configuring your AWS profile in `~/.aws/config`
- Testing your connection to Parameter Store

### 2. Connect to a Database

```bash
# Connect to postgres database in dev environment (default engine is postgres)
houlak-cli db-connect --env dev

# Connect to mariadb database
houlak-cli db-connect mariadb --env dev

# Connect with custom port
houlak-cli db-connect postgres --env dev --port 54321

# Connect with different AWS profile
houlak-cli db-connect --env dev --profile my-profile
```

### 3. Use Your Database Client

Once connected, use your favorite database client (DBeaver, TablePlus, pgAdmin, etc.) with:

```
Host: localhost
Port: 54320 (or your custom port)
```

Press `Ctrl+C` in the terminal to stop the tunnel.

## Available Commands

### `houlak-cli setup`

Run the interactive setup wizard to configure AWS profile and test connectivity.

### `houlak-cli db-connect [ENGINE] --env ENV [OPTIONS]`

Connect to a database through Session Manager.

**Arguments:**

- `ENGINE`: Database engine (default: postgres). Supported: postgres, mariadb

**Options:**

- `--env, -e`: Environment name (required). Examples: dev, qa, prod
- `--port, -p`: Local port number (optional, uses default based on engine)
- `--profile`: AWS profile name (default: houlak)

**Examples:**

```bash
houlak-cli db-connect --env dev
houlak-cli db-connect mariadb --env dev --port 33061
houlak-cli db-connect --env qa --profile my-profile
```

### `houlak-cli db-list [--profile PROFILE]`

List all available databases from Parameter Store.

```bash
houlak-cli db-list
houlak-cli db-list --profile my-profile
```

### `houlak-cli config-current`

Display current houlak-cli configuration.

```bash
houlak-cli config-current
```

### `houlak-cli config-list`

List all AWS profiles configured locally.

```bash
houlak-cli config-list
```

### `houlak-cli admin-db-add` (Admin only)

Add a database configuration to Parameter Store. Requires admin privileges.

```bash
houlak-cli admin-db-add hk-postgres-dev \
  --project hk \
  --engine postgres \
  --env dev \
  --bastion i-1234567890abcdef0 \
  --rds-endpoint hk-postgres-dev.region.rds.amazonaws.com \
  --rds-port 5432 \
  --region us-east-1
```

### `houlak-cli --help`

Show help for all commands.

### `houlak-cli --version` or `houlak-cli -v`

Show version information.

```bash
houlak-cli --version
# Output: houlak-cli version 0.1.0
```

## How It Works

### Database Connections

The `db-connect` command uses AWS Session Manager to create a secure tunnel from your local machine to your RDS database through a bastion host. This approach:

- ✅ Eliminates the need for SSH keys
- ✅ Doesn't require exposed SSH ports
- ✅ Provides full audit trail in CloudTrail
- ✅ Uses IAM-based authentication

The database configurations are stored securely in AWS Systems Manager Parameter Store.

### Future Tools

Additional tools and commands will be added to `houlak-cli` to support various AWS operations and developer workflows.

## Troubleshooting

### AWS CLI not found

Install AWS CLI v2 from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

### Session Manager Plugin not found

Install the plugin from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

### AWS Session expired

Run:

```bash
aws sso login --profile houlak
```

### Port already in use

Specify a different port:

```bash
houlak-cli db-connect --env dev --port 54321
```

### Database not found

Check available databases:

```bash
houlak-cli db-list
```

## Contributing

This is an internal tool for Houlak development team.

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions, contact the DevOps team or open an issue in the repository.
