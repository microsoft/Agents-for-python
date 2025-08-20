import inspect

def raise_if_empty_or_None(func_name, err=ValueError, **kwargs):
    s = ""
    for key, value in kwargs.items():
        if not value:
            s += f"\tArgument '{key}' is required and cannot be None or empty.\n"
    if s:
        header = f"{func_name}: called with empty arguments:"
        raise err(header + "\n" + s)