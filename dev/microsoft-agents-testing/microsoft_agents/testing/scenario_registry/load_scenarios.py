# In scenario_registry.py or a new cli/discovery.py

import importlib
import sys
from pathlib import Path

from .scenario_registry import scenario_registry

def load_scenarios(module_path: str) -> int:
    """Import a module to trigger scenario registration.
    
    Args:
        module_path: Python module path (e.g., "myproject.scenarios")
                     or file path (e.g., "./scenarios.py")
    
    Returns:
        Number of scenarios registered after import.
    
    Example:
        load_scenarios("myproject.scenarios")
        load_scenarios("./tests/scenarios.py")
    """
    before_count = len(scenario_registry)
    
    if module_path.endswith(".py") or "/" in module_path or "\\" in module_path:
        # File path - load as module
        path = Path(module_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")
        
        # Add parent to sys.path temporarily
        parent = str(path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)
        
        module_name = path.stem
        importlib.import_module(module_name)
    else:
        # Module path - import directly
        importlib.import_module(module_path)
    
    return len(scenario_registry) - before_count