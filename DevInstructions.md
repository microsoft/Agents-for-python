# Pre-Requisites
1. Clone the Git Repo at https://github.com/Microsoft/Agents-for-python
    ```
    git clone https://github.com/Microsoft/Agents-for-python
    ```
2. Download and Install [VS Code](https://code.visualstudio.com/download). 
3. Download and Install the [latest Python version](https://www.python.org/downloads/). 

4. Install Python extensions for VS Code (via VS Code)

# Instructions
1. Setup Python Virtual Environment. In VS Code, click the python version (bottom right) and create a virtual environment. 

1. Powershell needs to be set to allow running of scripts. Do this by opening powershell in Admin mode and running:
    ```
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```
1. Restart the Terminal in VSCode to pickup the new virtual envionrment.
1. Create the symlinks for debugging of the libraries. Be sure to do this as part of the terminal in VSCode, as it needs to use the Virtual Environment setup in the previous step. 
    ```
    pip install -e ./libraries/microsoft-agents-activity/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-hosting-core/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-authentication-msal/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-copilotstudio-client/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-hosting-aiohttp/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-hosting-teams/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-storage-blob/ --config-settings editable_mode=compat
    pip install -e ./libraries/microsoft-agents-storage-cosmos/ --config-settings editable_mode=compat    
    ```
1. Setup the dev dependencies for python. In the terminal, at the project root, run:
    ```
    pip install -r .\dev_dependencies.txt
    ```
1. Run the unit tests. From the terminal:
    ```
    pytest
    ```
1. In VSCode, click on the Testing icon on the far left and select 'Configure' and select the `pytest` option. 

# Setup Dev Tunnels
Before you can run an actual agent, you'll need to setup Dev-Tunnels. 
1. Install [Dev Tunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows).
    ```
    winget install Microsoft.devtunnel
    ```
1. Login to devtunnel
    ```
    devtunnel user login
    ```
2. Create the Tunnel (Note - use a unique name. Not 'my-tunnel')
    ```
    devtunnel create my-tunnel -a
    devtunnel port create -p 3978 my-tunnel
    ```
3. Run the tunnel
    ```
    devtunnel host -a my-tunnel
    ```
    Make sure you record / remember the URLs given on the host step. These are very handy later. 

# Create a new Agent (Bot) in the Azure Portal. 
In the Azure Portal, [create a new Agent](https://ms.portal.azure.com/#create/Microsoft.AzureBot). 
1. Single Tenant.
1. "Create new Microsoft App ID"
1. In the Config for the new Agent, set the Messaging Endpoint to the Tunnel endpoint. Be sure to append '/api/messages' to the end of the URL. 

# To do local testing, install the teams toolkit playground
* Install [TTK Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit). This is in the `Releases` section of the GitHub repo. 
2. Run the EXE. Launch the URL that gives the web interface. It'll be in the console. Something like:
```
http://localhost:56150/
```

# Run a local sample
1. In VSCode, go to the `test_samples` folder.
1. Open the `app_style` folder
1. select `empty_agent.py`
1. Hit the run button in the top right. 

Go over to the running TTK Playground in the browser (from the prevoius step) and chat with the Agent. 

# ToDo
* Axel. Add VSCode Settings to auto-ask / install the Python extension in VS Code. 
* Axel. Add VSCode file for the launch.json that points at the test / dev samples. Use defaults / no dependencies. 
* Add in the Testing 
* Chris. Delete old branches in the repo. 

