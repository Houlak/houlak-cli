# Houlak CLI

A command-line tool to simplify database connections through AWS Session Manager.

## Overview

`houlak-cli` is a developer-friendly tool that abstracts the complexity of connecting to RDS databases through AWS Session Manager. No need to understand AWS internals - just run a simple command and connect.

## Prerequisites

Before using `houlak-cli`, you need:

- **Python 3.8+**
- **AWS CLI v2** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS Session Manager Plugin** - [Installation Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

## Installation

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

## Quick Start

### 1. Initial Setup

Run the setup wizard to configure your AWS profile:

```bash
houlak-cli setup
```

The wizard will guide you through:

- Checking prerequisites (AWS CLI, Session Manager Plugin)
- Configuring your AWS profile
- Testing your connection

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

### `houlak-cli list [--profile PROFILE]`

List all available databases from Parameter Store.

```bash
houlak-cli list
houlak-cli list --profile my-profile
```

### `houlak-cli check [--profile PROFILE]`

Check prerequisites and configuration status.

```bash
houlak-cli check
houlak-cli check --profile my-profile
```

### `houlak-cli config show`

Display current configuration.

```bash
houlak-cli config show
```

### `houlak-cli config set KEY VALUE`

Set a configuration value.

```bash
houlak-cli config set default_profile houlak
houlak-cli config set default_port 54320
```

### `houlak-cli --help`

Show help for all commands.

### `houlak-cli --version`

Show version information.

## How It Works

`houlak-cli` uses AWS Session Manager to create a secure tunnel from your local machine to your RDS database through a bastion host. This approach:

- ✅ Eliminates the need for SSH keys
- ✅ Doesn't require exposed SSH ports
- ✅ Provides full audit trail in CloudTrail
- ✅ Uses IAM-based authentication

The database configurations are stored securely in AWS Systems Manager Parameter Store.

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
houlak-cli list
```

## Contributing

This is an internal tool for Houlak development team.

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions, contact the DevOps team or open an issue in the repository.
