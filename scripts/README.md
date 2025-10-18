# Scripts

This folder contains helpful scripts for development.

## Development Setup Scripts

Both of these scripts will create a Python environment based on the default version of `python` in your PATH. Ensure the version is at least 3.10 by running:

```bash
python --version
```

The virtual environment, by default, will created as a directory named `venv` that will be placed at the root of this project.

> Note: The SDK supports Python 3.10, 3.11, 3.12, 3.13, and 3.14.

### Windows

Powershell needs to be set to allow running of scripts. Do this by opening PowerShell in admin mode and running:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then, from the root directory, run:

```bash
. ./scripts/dev_setup.ps1
```

From the root of the project, you can activate the environment:

```bash
. ./venv/Scripts/activate
```

To deactivate:

```bash
deactivate
```

### Linux and macOS

From the root directory, run:

```bash
. ./scripts/dev_setup.sh
```

From the root of the project, you can activate the environment:

```bash
. ./venv/bin/activate
```

To deactivate:

```bash
deactivate
```

## Troubleshooting

If you encounter any issues, please create an issue on GitHub.