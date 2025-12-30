# Houlak CLI - Complete Project Generation Prompt

Use this prompt in a new Cursor Composer session to generate the complete project.

## Project Already Created

The following files have been created:

- houlak_cli/**init**.py
- houlak_cli/**main**.py
- houlak_cli/constants.py
- houlak_cli/utils.py
- houlak_cli/validators.py
- houlak_cli/config.py
- houlak_cli/aws_helper.py

## Files Still Needed

Please create the following files to complete the project:

### 1. houlak_cli/setup_wizard.py

Create an advanced setup wizard that:

- Guides users through AWS profile creation
- Writes to ~/.aws/config automatically
- Prompts for SSO Start URL, Account ID, Role Name, Region
- Executes aws sso login after configuration
- Tests Parameter Store access
- Lists available databases after setup

### 2. houlak_cli/db_connect.py

Create database connection module that:

- Accepts engine (postgres/mariadb), environment, port, profile as parameters
- Default engine is postgres
- Builds database name as: {project}-{engine}-{env}
  Examples: hk-postgres-dev, hk-mariadb-dev, creditel-postgres-dev
- Fetches config from Parameter Store
- Validates AWS session (runs sso login if expired)
- Checks if local port is available (suggests alternative if not)
- Starts SSM port forwarding
- Shows BASIC connection info (host, port only)
- Keeps tunnel open (blocks until Ctrl+C)

### 3. houlak_cli/cli.py

Create main CLI using Typer with these commands:

```python
@app.command()
def setup():
    """Run setup wizard to configure houlak-cli."""

@app.command()
def db_connect(
    engine: str = typer.Argument("postgres", help="Database engine"),
    env: str = typer.Option(..., "--env", "-e", help="Environment (dev/qa/prod)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Local port"),
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """Connect to database through Session Manager."""

@app.command()
def list(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """List available databases."""

@app.command()
def check(
    profile: str = typer.Option("houlak", "--profile", help="AWS profile"),
):
    """Check prerequisites and configuration."""

@app.command()
def config_show():
    """Show current configuration."""

@app.command()
def config_set(key: str, value: str):
    """Set configuration value."""
```

### 4. tests/test_validators.py

Create basic tests for validators module.

### 5. tests/test_config.py

Create basic tests for config module.

### 6. tests/test_cli.py

Create basic CLI tests with mocks.

### 7. setup.py

```python
from setuptools import setup, find_packages

setup(
    name="houlak-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]>=0.9.0",
        "boto3>=1.28.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "houlak-cli=houlak_cli.cli:app",
        ],
    },
    python_requires=">=3.8",
)
```

### 8. requirements.txt

```
typer[all]>=0.9.0
boto3>=1.28.0
rich>=13.0.0
pyyaml>=6.0
```

### 9. requirements-dev.txt

```
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
```

### 10. .gitignore

```
__pycache__/
*.pyc
.pytest_cache/
dist/
build/
*.egg-info/
.venv/
venv/
.env
.DS_Store
```

### 11. README.md

Create a comprehensive README with:

- Brief description
- Prerequisites (AWS CLI, Session Manager Plugin, Python 3.8+)
- Installation: `pip install git+https://github.com/Houlak/houlak-cli.git`
- Quick Start
- Available commands
- Brief explanation of what each command does

### 12. LICENSE

Add MIT License.

## Important Implementation Details

1. **Database Name Format**: `{project}-{engine}-{env}`

   - Examples: hk-postgres-dev, hk-mariadb-dev, creditel-postgres-dev

2. **Parameter Store Structure**:

   ```
   /houlak/cli/databases/hk-postgres-dev
   {
     "project": "hk",
     "engine": "postgres",
     "environment": "dev",
     "bastionInstanceId": "i-04fb222eb9ce090c0",
     "rdsEndpoint": "hk-postgres-dev.cgv7llbm9uex.us-east-1.rds.amazonaws.com",
     "rdsPort": 5432,
     "region": "us-east-1",
     "defaultProfile": "houlak",
     "defaultLocalPort": 54320
   }
   ```

3. **Connection Info Output** (BASIC):

   ```
   ✅ Connected to hk-postgres-dev!

   Database connection details:
     Host: localhost
     Port: 54320

   Press Ctrl+C to stop the tunnel.
   ```

4. **Error Handling**: Always offer interactive help when something fails

5. **Setup Wizard**: Should be advanced level - create AWS profile automatically

6. **Code Quality**:
   - Use type hints
   - Add docstrings
   - Clean, well-documented code
   - Proper error handling

Create all the missing files to complete the project!


