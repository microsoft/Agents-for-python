import pathlib

_AGENTS_DIR_NAME + "_agents"
AGENTS_PATH = pathlib.Path(__file__).parent.parent.resolve() / _AGENTS_DIR_NAME
ENTRY_POINT_NAME = "run_agent.ps1"

breakpoint()