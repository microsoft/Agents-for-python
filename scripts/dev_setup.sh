if command -v python >/dev/null 2>&1
then
    PYTHON=python
elif command -v python3 >/dev/null 2>&1
then
    PYTHON=python3
else
    echo "Error: neither 'python' nor 'python3' was found on PATH." >&2
    return 1 2>/dev/null || exit 1
fi

$PYTHON -m venv venv

. ./venv/bin/activate

pip install -e ./libraries/microsoft-agents-activity/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-entra-auth-sidecar/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-copilotstudio-client/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-teams/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-msteams/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-dialogs/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-fastapi/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-slack/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-blob/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-cosmos/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-testing/ --config-settings editable_mode=compat

pip install -r dev_dependencies.txt

pre-commit install