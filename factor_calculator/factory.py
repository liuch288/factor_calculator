"""
Factory module for creating DMU and PEU instances from string specifications.

This module parses strings like "KlineDMU(45)" or "BiquotePEU(watching_time=60)" 
and dynamically creates the corresponding Unit instances using importlib.

Supports both rbt and lrbt modules. When a class is not found in rbt,
it falls back to lrbt for lookup.
"""

import ast
import importlib
import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union

# Module bases to search. rbt is checked first (backward compatible),
# lrbt is used as fallback for extended classes.
MODULE_BASES = ["rbt", "lrbt"]

# Maps class suffix to module path suffix (e.g., "DMU" -> "dmu")
SUFFIX_MODULES = {
    "DMU": "dmu",
    "PEU": "peu",
}


class _LazyClassStub:
    """
    Placeholder for a class found via AST but unimportable due to missing deps.
    Retries real import and caches the result on first attribute access.
    """
    def __init__(self, module_path: str, class_name: str):
        self._module_path = module_path
        self._class_name = class_name
        self._cls = None

    def _resolve(self):
        if self._cls is None:
            self._cls = importlib.import_module(self._module_path)
            self._cls = getattr(self._cls, self._class_name)
        return self._cls

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __repr__(self):
        return f"<lazy stub: {self._module_path}.{self._class_name}>"

    @property
    def __name__(self):
        return self._class_name


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


def _get_submodule_name(class_name: str) -> str:
    """
    Derive a submodule name from a class name.
    E.g., "KlineDMU" -> "kline", "PositionPnlDMU" -> "position_pnl", "AtrDMU" -> "atr"
    """
    base = class_name
    for suffix in ["DMU", "PEU"]:
        if base.endswith(suffix):
            base = base[:-len(suffix)].rstrip("_")
            break
    return base.lower()


def get_module_for_class(class_name: str) -> Tuple[Type, str]:
    """
    Determine which module to import based on class name suffix.

    Searches MODULE_BASES in order (rbt first, then lrbt), trying both
    direct module lookup and submodule patterns.

    Args:
        class_name: The class name (e.g., "KlineDMU", "AtrDMU", "BiquotePEU")

    Returns:
        Tuple of (module, module_path)

    Raises:
        ValueError: If the class suffix is not recognized
    """
    # Determine module suffix
    module_suffix = None
    for suffix in SUFFIX_MODULES:
        if class_name.endswith(suffix):
            module_suffix = SUFFIX_MODULES[suffix]
            break

    if module_suffix is None:
        raise ValueError(
            f"Unknown class suffix for '{class_name}'. "
            "Expected class names ending with 'DMU' or 'PEU'"
        )

    # Derive submodule name: e.g., "AtrDMU" -> "atr"
    submodule_base = _get_submodule_name(class_name)
    # Submodule patterns: [direct class in main module, _suffix variant in submodule, bare submodule]
    submodule_patterns = [
        f"{submodule_base}_dmu",
        submodule_base,
        f"{submodule_base}_peu",
    ]

    # Try each module base (rbt first, then lrbt)
    for base in MODULE_BASES:
        main_module_path = f"{base}.{module_suffix}"

        # Try direct class in main module
        try:
            module = importlib.import_module(main_module_path)
            if hasattr(module, class_name):
                return module, main_module_path
        except ImportError:
            pass

        # Try submodules
        for sub_pattern in submodule_patterns:
            sub_module_path = f"{base}.{module_suffix}.{sub_pattern}"
            try:
                submod = importlib.import_module(sub_module_path)
                if hasattr(submod, class_name):
                    return submod, sub_module_path
            except ImportError:
                continue

    # If not found, return the first (rbt) main module as fallback
    # and let create_unit do a deeper search
    try:
        module = importlib.import_module(f"rbt.{module_suffix}")
        return module, f"rbt.{module_suffix}"
    except ImportError:
        pass

    raise ValueError(f"Could not find module for class '{class_name}'")


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

    # Search all module bases for the class (deep fallback in all submodules)
    # Use pkgutil.iter_modules to scan submodule files, since dir() only
    # returns top-level module attributes and submodules may not be imported yet.
    import pkgutil

    def _find_class_in_module(mod, class_name):
        """Check module and its submodules for a class."""
        # Check direct attributes
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and attr.__name__ == class_name:
                return attr
        # Scan submodule files via pkgutil
        if hasattr(mod, '__path__'):  # it's a package
            for importer, subname, ispkg in pkgutil.iter_modules(mod.__path__, mod.__name__ + '.'):
                if ispkg:
                    continue
                try:
                    submod = importlib.import_module(subname)
                    for attr_name in dir(submod):
                        attr = getattr(submod, attr_name)
                        if isinstance(attr, type) and attr.__name__ == class_name:
                            return attr
                except (ImportError, Exception):
                    # Fall back: find class via AST scan without loading
                    import os
                    spec = importlib.util.find_spec(subname)
                    if spec and spec.origin and os.path.exists(spec.origin):
                        try:
                            with open(spec.origin) as fh:
                                src = fh.read()
                            tree = ast.parse(src)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef) and node.name == class_name:
                                    # Return a helper that will retry real import at instantiation time
                                    return _LazyClassStub(subname, class_name)
                        except (SyntaxError, OSError):
                            pass
        return None

    if cls is None:
        for base in MODULE_BASES:
            for suffix in ["dmu", "peu"]:
                try:
                    mod = importlib.import_module(f"{base}.{suffix}")
                    found = _find_class_in_module(mod, class_name)
                    if found is not None:
                        cls = found
                        break
                except ImportError:
                    continue
            if cls is not None:
                break

    if cls is None:
        raise ValueError(
            f"Class '{class_name}' not found. "
            f"Checked modules: rbt.dmu, rbt.peu, lrbt.dmu, lrbt.peu and their submodules."
        )

    # Parse parameters
    positional, keyword = parse_parameters(params_str)
    
    # Create instance
    try:
        return cls(*positional, **keyword)
    except TypeError as e:
        raise ValueError(
            f"Failed to instantiate '{class_name}' with args {positional}, kwargs {keyword}: {e}"
        )


def parse_parameters(params_str: str) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Parse a parameter string into positional args and keyword args.
    
    Examples:
        >>> parse_parameters("45")
        ([45], {})
        >>> parse_parameters("interval=5, start_time=9:30")
        ([], {'interval': 5, 'start_time': datetime.time(9, 30)})
        >>> parse_parameters("1, watching_time=60")
        ([1], {'watching_time': 60})
    
    Args:
        params_str: Parameter string (e.g., "45" or "interval=5, start_time=9:30")
        
    Returns:
        Tuple of (positional_args, keyword_args)
    """
    params_str = params_str.strip()
    if not params_str:
        return [], {}
    
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
    
    positional = []
    keyword = {}
    
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            keyword[key.strip()] = parse_value(value.strip())
        else:
            positional.append(parse_value(arg))
    
    return positional, keyword


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
    Get list of available DMU or PEU classes from both rbt and lrbt modules.

    Args:
        suffix: Filter by suffix ("DMU" or "PEU"), or None for all

    Returns:
        List of class names
    """
    from rbt.dmu import DecisionMakingUnit
    from rbt.peu import PnlEstimateUnit

    classes = []

    if suffix is None or suffix == "DMU":
        for base in MODULE_BASES:
            for mod_name, parent_cls in [("rbt.dmu", DecisionMakingUnit)]:
                try:
                    mod = importlib.import_module(f"{base}.dmu")
                    for name in dir(mod):
                        obj = getattr(mod, name)
                        if isinstance(obj, type) and issubclass(obj, parent_cls) and obj != parent_cls:
                            classes.append(name)
                except ImportError:
                    pass

    if suffix is None or suffix == "PEU":
        for base in MODULE_BASES:
            try:
                mod = importlib.import_module(f"{base}.peu")
                for name in dir(mod):
                    obj = getattr(mod, name)
                    if isinstance(obj, type) and issubclass(obj, PnlEstimateUnit) and obj != PnlEstimateUnit:
                        classes.append(name)
            except ImportError:
                pass

    return sorted(set(classes))
