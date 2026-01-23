from .underscore import Underscore

def check(underscore: Underscore, *args, **kwargs) -> tuple[bool, str]:
    """Evaluate and return (result, explanation)."""
    try:
        result = underscore(*args, **kwargs)
        if result:
            return True, f"{underscore!r} passed"
        else:
            return False, f"{underscore!r} failed for {args}"
    except Exception as e:
        return False, f"{underscore!r} raised {e}"