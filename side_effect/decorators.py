import inspect
from copy import deepcopy
from typing import Any, Callable, Dict, List, Union


def _get_arg_names(func: Callable) -> List[str]:
    return inspect.getfullargspec(func)[0]


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
        arg_names = _get_arg_names(func)
        gen = (f"{arg_name}: {previous_state}"
               for arg_name, previous_state in zip(arg_names, previous_states))
        print(f"Call of {func.__qualname__} on args "
              f"{tuple(gen)}:")
        result = func(*args)
        found = False
        for arg, previous_state, arg_name in zip(args, previous_states,
                                                 arg_names):
            if hasattr(arg, "__dict__"):
                diff = _get_top_level_diff(arg, previous_state)
                if not diff:
                    continue
                for key, attr in diff.items():
                    print(f"    Attribute {key} of {str(arg_name)}"
                          " changed"
                          f" from {str(getattr(previous_state, key))}"
                          f" to {str(attr)}.")
                    found = True
            else:
                if arg != previous_state:
                    print(f"    Argument {str(arg_name)} changed"
                          f" from {str(previous_state)}"
                          f" to {str(arg)}.")
                    found = True
        if not found:
            print("    No side effects found.")
        return result
    return g


def deep_se_print(func: Callable) -> Callable:
    """Transforms the function to print nested side effects.

    Searches recursively for changes on deep inner attributes of the arguments.

    Goes down a tree until it finds some element which has no __dict__. For
    each element of the tree, if it has no __dict__ or if __eq__ is
    user-defined, it verifies equality (==/__eq__) with the previous state.
    """
    def g(*args):
        previous_states = deepcopy(args)
        arg_names = [str(previous_state) for previous_state in previous_states]
        gen = (f"{previous_state}"
               for previous_state in previous_states)
        print(f"Call of {func.__qualname__} on args "
              f"{tuple(gen)}:")
        result = func(*args)
        search_recursive(args, previous_states, arg_names)
        return result

    def search_recursive(args, previous_states, arg_names,
                         tree: str = ""):
        for arg, previous_state, arg_name in zip(args,
                                                 previous_states, arg_names):
            if (not hasattr(previous_state, "__dict__")
                    or _has_eq_defined(previous_state)):
                if arg != previous_state:
                    print(f"    {str(arg_name)}{tree} changed"
                          f" from {str(previous_state)}"
                          f" to {str(arg)}.")
            else:
                tree = f" of {arg}" + tree
                for key, attr in vars(arg).items():
                    if not hasattr(attr, "__dict__"):
                        if attr != getattr(previous_state, key):
                            print(f"    {str(key)}{tree}"
                                  f" changed"
                                  f" from {str(getattr(previous_state, key))}"
                                  f" to {str(attr)}.")
                        continue
                    search_recursive(tuple(vars(attr).values()),
                                     tuple(
                                        vars(getattr(previous_state,
                                                     key)).values()
                                        ),
                                     vars(attr).keys(),
                                     f" of {str(attr)}" + tree)
    return g


def ret_print(func: Callable) -> Callable:
    """Transforms the function to print its returned value."""
    def g(*args):
        result = func(*args)
        print(str(result))
        return result
    return g
