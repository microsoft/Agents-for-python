python -m venv venv

. .\venv\Scripts\Activate.ps1

pip install -e ./libraries/microsoft-agents-activity/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-copilotstudio-client/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-hosting-teams/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-blob/ --config-settings editable_mode=compat
pip install -e ./libraries/microsoft-agents-storage-cosmos/ --config-settings editable_mode=compat

pip install -r dev_dependencies.txt

pre-commit install