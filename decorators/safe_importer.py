import importlib
import logging
from types import ModuleType
from typing import Optional, Dict, Any

def safe_import(
    module_name: str,
    alias: Optional[str] = None,
    globals_dict: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
    overwrite: bool = True,
) -> Optional[ModuleType]:
    """
    Safely import a module and add it to the globals.
    
    Args:
        module_name: Name of the module to import
        alias: Optional alternative name to use in globals
        globals_dict: Dictionary to add the module to (defaults to caller's globals)
        logger: Optional logger to use for errors
        overwrite: If True, allows overwriting existing globals
        
    Returns:
        The imported module or None if import failed
    """
    
    # Use the caller's globals if none provided
    if globals_dict is None:
        import inspect
        frame = inspect.currentframe().f_back
        globals_dict = frame.f_globals
    
    # Set up logger if not provided
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Try to import the module directly with error handling
    try:
        module = importlib.import_module(module_name)
        
        # Handle nested modules - import the top-level module too
        if '.' in module_name:
            top_module_name = module_name.split('.')[0]
            top_module = importlib.import_module(top_module_name)
            
            # Add top-level module to globals if not already there or if overwriting is allowed
            if top_module_name not in globals_dict or overwrite:
                globals_dict[top_module_name] = top_module
    except Exception as e:
        logger.error(f"Error importing {module_name}: {e}")
        return None
    
    # Determine the name to use in globals
    name_in_globals = alias if alias is not None else module_name
    
    # Add to globals if not already there or if overwriting is allowed
    if name_in_globals not in globals_dict or overwrite:
        globals_dict[name_in_globals] = module
    
    return module