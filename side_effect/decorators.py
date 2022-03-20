from copy import deepcopy
from typing import Any, Callable, Dict, Union


def _has_eq_defined(obj: Any) -> bool:
    return hasattr(obj.__eq__, "__func__")


def _get_top_level_diff(new: Any, old: Any) -> Dict[str, Any]:
    if not isinstance(old, type(new)):
        raise ValueError("Trying to check diff of incompatible types.")
    new_attrs = vars(new)
    old_attrs = vars(old)
    diff: Dict[str, Any] = {}
    for key, attr in new_attrs.items():
        if ((key not in old_attrs or attr != old_attrs[key])):
            if not hasattr(attr, "__dict__") or _has_eq_defined(attr):
                diff[key] = deepcopy(attr)
    return diff


def se_print(func: Callable) -> Callable:
    """Transforms the function to print its side-effects on the arguments."""
    def g(*args):
        previous_states = deepcopy(args)
        print(f"Call of {func.__name__} on args "
              f"{tuple((str(arg) for arg in args))}:")
        result = func(*args)
        found = False
        for arg, previous_state in zip(args, previous_states):
            if hasattr(arg, "__dict__"):
                diff = _get_top_level_diff(arg, previous_state)
                if not diff:
                    continue
                for key, attr in diff.items():
                    print(f"    Attribute {key} of {str(arg)} changed"
                          f" from {str(getattr(previous_state, key))}"
                          f" to {str(attr)}.")
                    found = True
            else:
                if arg != previous_state:
                    print(f"    Argument {str(arg)} changed"
                          f" from {str(previous_state)}"
                          f" to {str(arg)}.")
        if not found:
            print("    No side effects found.")
        return result
    return g


def ret_print(func: Callable) -> Callable:
    """Transforms the function to print its returned value."""
    def g(*args):
        result = func(*args)
        print(str(result))
        return result
    return g
