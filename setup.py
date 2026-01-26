"""Setup configuration for houlak-cli package."""

from setuptools import find_packages, setup

setup(
    name="houlak-cli",
    version="0.1.1",
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




