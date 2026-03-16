"""
Factory module for creating DMU and PEU instances from string specifications.

This module parses strings like "KlineDMU(45)" or "BiquotePEU(watching_time=60)" 
and dynamically creates the corresponding Unit instances using importlib.
"""

import importlib
import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union


def parse_unit_spec(spec: str) -> Tuple[str, str]:
    """
    Parse a unit specification string into class name and parameters.
    
    Examples:
        "KlineDMU(45)" -> ("KlineDMU", "45")
        "BiquotePEU(watching_time=60)" -> ("BiquotePEU", "watching_time=60")
        "SimpleDMU" -> ("SimpleDMU", "")
    
    Args:
        spec: Unit specification string, e.g., "KlineDMU(45)"
        
    Returns:
        Tuple of (class_name, params_str)
    """
    spec = spec.strip()
    
    # Check if there are parentheses
    if "(" in spec:
        # Split on first "(" to get class name
        class_name = spec.split("(")[0]
        # Get content between parentheses
        # Handle nested parentheses properly
        paren_depth = 0
        params_start = spec.find("(")
        params_end = params_start
        for i, char in enumerate(spec):
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    params_end = i
                    break
        
        params_str = spec[params_start + 1:params_end].strip()
        return class_name, params_str
    else:
        return spec, ""


def get_module_for_class(class_name: str) -> Tuple[Type, str]:
    """
    Determine which module to import based on class name suffix.
    
    Args:
        class_name: The class name (e.g., "KlineDMU", "BiquotePEU")
        
    Returns:
        Tuple of (module, module_path)
        
    Raises:
        ValueError: If the class suffix is not recognized
    """
    if class_name.endswith("DMU"):
        module_path = "rbt.dmu"
    elif class_name.endswith("PEU"):
        module_path = "rbt.peu"
    else:
        raise ValueError(
            f"Unknown class suffix for '{class_name}'. "
            "Expected class names ending with 'DMU' or 'PEU'"
        )
    
    module = importlib.import_module(module_path)
    
    # Check if class is in module directly
    if hasattr(module, class_name):
        return module, module_path
    
    # Try to import from submodules
    # This handles cases like KlineDMU which is in rbt.dmu.kline_dmu
    try:
        submodule_name = class_name.lower().replace("peu", "").replace("dmu", "").rstrip("_")
        if not submodule_name:
            # e.g., PositionPnlDMU -> position_pnl
            submodule_name = class_name[:-3].lower()
        
        # Try various submodule patterns
        for pattern in [
            f"rbt.dmu.{submodule_name}_dmu",
            f"rbt.dmu.{submodule_name}",
            f"rbt.peu.{submodule_name}_peu",
            f"rbt.peu.{submodule_name}",
        ]:
            try:
                submod = importlib.import_module(pattern)
                if hasattr(submod, class_name):
                    return submod, pattern
            except ImportError:
                continue
    except Exception:
        pass
    
    # Fall back to returning the main module
    return module, module_path


def create_unit(spec: str) -> Any:
    """
    Create a Unit instance from a specification string.
    
    Examples:
        >>> unit = create_unit("KlineDMU(45)")
        >>> unit = create_unit("BiquotePEU(watching_time=60)")
        >>> unit = create_unit("PositionPnlDMU")
    
    Args:
        spec: Unit specification string, e.g., "KlineDMU(45)"
        
    Returns:
        An instance of the specified Unit subclass
        
    Raises:
        ValueError: If the class cannot be found or instantiated
    """
    class_name, params_str = parse_unit_spec(spec)
    
    # Get the module
    module, module_path = get_module_for_class(class_name)
    
    # Get the class from module
    cls = None
    
    # Try direct attribute access first
    if hasattr(module, class_name):
        cls = getattr(module, class_name)
    else:
        # Try to find in submodules by importing them all
        # This is a fallback for classes not exported in __init__.py
        import rbt.dmu as dmu_module
        import rbt.peu as peu_module
        
        for mod in [dmu_module, peu_module]:
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and attr.__name__ == class_name:
                    cls = attr
                    break
            if cls:
                break
    
    if cls is None:
        raise ValueError(
            f"Class '{class_name}' not found. "
            f"Checked modules: rbt.dmu, rbt.peu and their submodules."
        )
    
    # Parse parameters
    params = parse_parameters(params_str)
    
    # Create instance
    try:
        return cls(**params)
    except TypeError as e:
        raise ValueError(
            f"Failed to instantiate '{class_name}' with params {params}: {e}"
        )


def parse_parameters(params_str: str) -> Dict[str, Any]:
    """
    Parse a parameter string into a dictionary.
    
    Examples:
        >>> parse_parameters("45")
        {}
        >>> parse_parameters("interval=5, start_time=9:30")
        {'interval': 5, 'start_time': datetime.time(9, 30)}
        >>> parse_parameters("watching_time=60")
        {'watching_time': 60}
    
    Args:
        params_str: Parameter string (e.g., "45" or "interval=5, start_time=9:30")
        
    Returns:
        Dictionary of parameter name to value
    """
    params_str = params_str.strip()
    if not params_str:
        return {}
    
    # Check if it's a single positional argument (no keyword args)
    # For cases like "KlineDMU(45)" where 45 is a positional arg
    if "=" not in params_str:
        # Try to parse as a single value
        try:
            # Try as integer
            return {"value": int(params_str)}
        except ValueError:
            try:
                # Try as float
                return {"value": float(params_str)}
            except ValueError:
                # Keep as string
                return {"value": params_str}
    
    # Parse keyword arguments
    params = {}
    
    # Split by comma, but respect parentheses
    args = []
    current = ""
    paren_depth = 0
    for char in params_str:
        if char == "(":
            paren_depth += 1
            current += char
        elif char == ")":
            paren_depth -= 1
            current += char
        elif char == "," and paren_depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char
    
    if current.strip():
        args.append(current.strip())
    
    for arg in args:
        if "=" not in arg:
            continue
        
        key, value = arg.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Parse value
        params[key] = parse_value(value)
    
    return params


def parse_value(value_str: str) -> Any:
    """
    Parse a value string into Python value.
    
    Examples:
        >>> parse_value("60")
        60
        >>> parse_value("3.14")
        3.14
        >>> parse_value("True")
        True
        >>> parse_value("9:30")
        datetime.time(9, 30)
        >>> parse_value("datetime.time(9, 30)")
        datetime.time(9, 30)
    
    Args:
        value_str: String representation of a value
        
    Returns:
        Parsed Python value
    """
    # Handle None
    if value_str == "None":
        return None
    
    # Handle booleans
    if value_str == "True":
        return True
    if value_str == "False":
        return False
    
    # Try integer
    try:
        return int(value_str)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value_str)
    except ValueError:
        pass
    
    # Try parsing time (e.g., "9:30" or "09:30:00")
    time_match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', value_str)
    if time_match:
        import datetime
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        second = int(time_match.group(3)) if time_match.group(3) else 0
        return datetime.time(hour, minute, second)
    
    # Try parsing datetime (e.g., "datetime.time(9, 30)")
    if value_str.startswith("datetime.time("):
        import datetime
        # Extract the arguments
        inner = value_str[len("datetime.time("):-1]
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) == 2:
            return datetime.time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return datetime.time(int(parts[0]), int(parts[1]), int(parts[2]))
    
    # Return as string (strip quotes if present)
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]
    
    return value_str


def create_units(specs: List[str]) -> List[Any]:
    """
    Create multiple Unit instances from specification strings.
    
    Args:
        specs: List of unit specification strings
        
    Returns:
        List of Unit instances
    """
    return [create_unit(spec) for spec in specs]


# Convenience functions for common operations
def get_available_classes(suffix: str = None) -> List[str]:
    """
    Get list of available DMU or PEU classes.
    
    Args:
        suffix: Filter by suffix ("DMU" or "PEU"), or None for all
        
    Returns:
        List of class names
    """
    from rbt.dmu import DecisionMakingUnit
    from rbt.peu import PnlEstimateUnit
    
    classes = []
    
    if suffix is None or suffix == "DMU":
        # Get DMU classes from module
        import rbt.dmu as dmu_module
        for name in dir(dmu_module):
            obj = getattr(dmu_module, name)
            if isinstance(obj, type) and issubclass(obj, DecisionMakingUnit) and obj != DecisionMakingUnit:
                classes.append(name)
        
        # Also check submodules that may not be in __init__.py
        try:
            import rbt.dmu.kline_dmu as kline_module
            if hasattr(kline_module, 'KlineDMU'):
                if 'KlineDMU' not in classes:
                    classes.append('KlineDMU')
        except ImportError:
            pass
    
    if suffix is None or suffix == "PEU":
        import rbt.peu as peu_module
        for name in dir(peu_module):
            obj = getattr(peu_module, name)
            if isinstance(obj, type) and issubclass(obj, PnlEstimateUnit) and obj != PnlEstimateUnit:
                classes.append(name)
    
    return sorted(set(classes))
