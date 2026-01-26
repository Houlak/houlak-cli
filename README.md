# Houlak CLI

A comprehensive command-line tool suite for developers to interact with AWS services.

## Overview

`houlak-cli` is a developer-friendly toolkit designed for internal use at Houlak. The tool provides multiple utilities for interacting with AWS services, abstracting the complexity of AWS operations and allowing developers to focus on their work without needing to understand AWS internals.

### Current Tools

**Database Connection Tool**: Connect securely to RDS databases through a bastion host using AWS Session Manager. The tool handles all the complexity of establishing secure connections, so you don't have to worry about SSH keys, exposed ports, or connection details.

### Future Tools

This is an extensible platform designed to grow. More tools and commands will be added in the future to support various AWS operations and developer workflows.

## Key Features

- **Pre-configured Databases**: Databases are configured by administrators in AWS Systems Manager Parameter Store, and developers can connect to them with simple commands
- **Bastion Host Transparency**: When you run the `db-connect` command, the console stays occupied maintaining an active tunnel connection through the bastion host (EC2 instance)
- **No Manual Bastion Configuration**: When connecting from your database client (DBeaver, TablePlus, pgAdmin, etc.), you don't need to specify the bastion host - the tool handles this automatically
- **Secure Connections**: Uses AWS Session Manager instead of traditional SSH, eliminating the need for SSH keys and exposed ports
- **IAM-based Authentication**: Full audit trail through CloudTrail

## Prerequisites

Before using `houlak-cli`, you need:

- **Python 3.8+**
- **pipx** - Recommended for isolated CLI installation. [Installation Guide](https://pipx.pypa.io/stable/installation/)
- **AWS CLI v2** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS Session Manager Plugin** - [Installation Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
- **AWS Profile Configuration** - `houlak-cli` is based on AWS profiles configured locally in `~/.aws/config`. You can configure it manually or use the `config` command.

## Installation

### First-time Installation

**Recommended: Using pipx** (ensures isolated environment)

```bash
pipx install git+https://github.com/Houlak/houlak-cli.git
```

Or clone and install in development mode:

```bash
git clone https://github.com/Houlak/houlak-cli.git
cd houlak-cli
pipx install -e .
```

### Updating to Latest Version

If you installed with pipx:

```bash
pipx upgrade houlak-cli
```

Or if installed in development mode:

```bash
cd houlak-cli
git pull origin main
pipx install -e .
```

### Check Current Version

Check which version you have installed:

```bash
houlak-cli --version
# or
houlak-cli -v
```

## Quick Start

### 1. Initial Configuration

**Important**: `houlak-cli` is based on AWS profiles configured locally in `~/.aws/config`. The first step is to have your AWS profile configured for the account you want to connect to.

Run the configuration wizard to set up your AWS profile:

```bash
houlak-cli config
```

The wizard will guide you through:

- Checking prerequisites (AWS CLI, Session Manager Plugin)
- Configuring your AWS profile in `~/.aws/config`
- Testing your connection to Parameter Store

### 2. Connect to a Database

Connect to a database by specifying its name from Parameter Store:

```bash
# Connect to a database using its name
houlak-cli db-connect --database hk-postgres-dev

# Connect with a different AWS profile
houlak-cli db-connect --database hk-postgres-dev --profile my-profile

# Connect with custom port
houlak-cli db-connect --database hk-mariadb-qa --port 33061
```

You can list available databases first:

```bash
houlak-cli db-list
```

**Important**: Once you run the `db-connect` command, your terminal will be occupied maintaining the tunnel connection. This is expected behavior - the tunnel must remain active while you use your database client. Press `Ctrl+C` when you're done to close the tunnel.

### 3. Use Your Database Client

Once connected, use your favorite database client (DBeaver, TablePlus, pgAdmin, etc.) to connect to:

```
Host: localhost
Port: (the port shown in the terminal, default varies by engine)
```

**Note**: You don't need to configure any bastion host settings in your database client - the tunnel is already established and handles this automatically.

Press `Ctrl+C` in the terminal to stop the tunnel when you're finished.

---

## For Administrators: Adding Databases

If you are an administrator, you can add new database configurations to Parameter Store so developers can connect to them.

### Adding a Database Configuration

Run the interactive command:

```bash
houlak-cli admin-db-add
```

The command will prompt you for:
- Database name (e.g., `hk-postgres-dev`)
- Project name
- Database engine (postgres/mariadb)
- Environment (dev/qa/prod)
- Bastion EC2 instance ID
- RDS endpoint
- RDS port
- AWS region

**Example:**

```bash
houlak-cli admin-db-add

# You'll be prompted for:
Database name: hk-postgres-dev
Project name: hk
Database engine: postgres
Environment: dev
Bastion EC2 instance ID: i-1234567890abcdef0
RDS endpoint: hk-postgres-dev.us-east-1.rds.amazonaws.com
RDS port: 5432
AWS region: us-east-1
```

Once added, developers can connect using:

```bash
houlak-cli db-connect --database hk-postgres-dev --profile <their-profile>
```

**Note**: The `admin-db-add` command requires admin privileges. Contact DevOps if you need admin access.

## Available Commands

### Configuration Commands

These commands work with AWS profiles configured locally:

#### `houlak-cli config`

Run the interactive configuration wizard to set up your AWS profile.

```bash
houlak-cli config
```

#### `houlak-cli config-list`

List all AWS profiles configured locally in `~/.aws/config`.

```bash
houlak-cli config-list
```

#### `houlak-cli config-current`

Display current AWS profile configuration for houlak-cli.

```bash
houlak-cli config-current
```

### Database Commands

#### `houlak-cli db-connect --database DATABASE_NAME [OPTIONS]`

Connect to a database through Session Manager via bastion host.

**Required Options:**

- `--database, -d`: Database name from Parameter Store (e.g., `hk-postgres-dev`)

**Optional:**

- `--profile`: AWS profile name (default: houlak)
- `--port, -p`: Local port number (optional, uses default based on engine)

**Examples:**

```bash
# Connect to a database
houlak-cli db-connect --database hk-postgres-dev

# Connect with a specific profile
houlak-cli db-connect --database hk-postgres-dev --profile my-profile

# Connect with custom port
houlak-cli db-connect --database hk-mariadb-qa --port 33061
```

#### `houlak-cli db-list [--profile PROFILE]`

List all available databases from Parameter Store.

```bash
houlak-cli db-list
houlak-cli db-list --profile my-profile
```

### Admin Commands

#### `houlak-cli admin-db-add [--profile PROFILE]` (Admin only)

Add a database configuration to Parameter Store interactively. Requires admin privileges.

This command will prompt you for all required information:
- Database name
- Project name
- Database engine (postgres/mariadb)
- Environment (dev/qa/prod)
- Bastion EC2 instance ID
- RDS endpoint
- RDS port
- AWS region

**Example:**

```bash
# Run the interactive command (uses default profile 'houlak')
houlak-cli admin-db-add

# Use a different profile for storing the configuration
houlak-cli admin-db-add --profile admin-profile
```

**Note**: This command is restricted to admin users only. Contact DevOps if you need admin access.

### `houlak-cli --help` or `houlak-cli -h`

Show help for all commands.

### `houlak-cli --version` or `houlak-cli -v`

Show version information.

```bash
houlak-cli --version
# or
houlak-cli -v
# Output: houlak-cli version 0.1.0
```

## How It Works

### Database Connections

The `db-connect` command uses AWS Session Manager to create a secure tunnel from your local machine to your RDS database through a bastion host (EC2 instance). 

**How the connection works:**

1. An administrator adds database configurations to AWS Parameter Store using `admin-db-add`
2. You run `houlak-cli db-connect --database hk-postgres-dev --profile your-profile`
3. The CLI reads the database configuration from Parameter Store
4. The CLI establishes a tunnel through the bastion host to the RDS database using your AWS profile
5. Your terminal stays occupied maintaining this tunnel (this is expected and necessary)
6. You connect your database client to `localhost` on the assigned port
7. Your database client doesn't need to know about the bastion host - it just connects to localhost
8. When you're done, press `Ctrl+C` to close the tunnel

**Benefits of this approach:**

- ✅ Eliminates the need for SSH keys
- ✅ Doesn't require exposed SSH ports
- ✅ Provides full audit trail in CloudTrail
- ✅ Uses IAM-based authentication
- ✅ No need to configure bastion host in your database client
- ✅ Developers use their own AWS profiles
- ✅ Centralized database configuration management

The database configurations (bastion host details, RDS endpoints, etc.) are stored securely in AWS Systems Manager Parameter Store by administrators and can be used by any developer with their own AWS profile.

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


