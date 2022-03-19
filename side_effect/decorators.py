from copy import deepcopy
from typing import Any, Callable, Dict, Union


def _get_top_level_diff(new: Any, old: Any) -> Union[Dict[str, Any], None]:
    if not isinstance(old, type(new)):
        raise ValueError("Trying to check diff of incompatible types.")
    if not hasattr(old, "__dict__"):
        return None
    new_attrs = vars(new)
    old_attrs = vars(old)
    diff: Dict[str, Any] = {}
    for key, attr in new_attrs.items():
        if key not in old_attrs or attr != old_attrs[key]:
            diff[key] = deepcopy(attr)
    return diff


def se_print(func: Callable) -> Callable:
    """Transforms the function to print its side-effects on the arguments."""
    def g(*args):
        previous_states = deepcopy(args)
        print(f"Call of {func.__name__} on args "
              f"{tuple((str(arg) for arg in args))}:")
        result = func(*args)
        for arg, previous_state in zip(args, previous_states):
            diff = _get_top_level_diff(arg, previous_state)
            if diff is None:
                continue
            for key, attr in diff.items():
                print(f"    Attribute {key} of {str(arg)} changed"
                      f" from {str(getattr(previous_state, key))}"
                      f" to {str(attr)}.")
        return result
    return g


def ret_print(func: Callable) -> Callable:
    """Transforms the function to print its returned value."""
    def g(*args):
        result = func(*args)
        print(str(result))
        return result
    return g
