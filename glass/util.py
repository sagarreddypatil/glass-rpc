def _pretty(s):
    if isinstance(s, bytes):
        return f"<{len(s)} bytes>"
    if isinstance(s, list):
        return list(map(_pretty, s))
    if isinstance(s, dict):
        return {k: _pretty(v) for k, v in s.items()}
    if isinstance(s, tuple):
        return tuple(map(_pretty, s))
    if isinstance(s, set):
        return set(map(_pretty, s))
    if isinstance(s, str):
        if len(s) > 10:
            return f"{s[:10]}..."
        return s
    return s

def pretty(s):
    return str(_pretty(s))


def fmt_args_kwargs(args, kwargs):
    args = [f"{pretty(arg)}" for arg in args]
    kwargs = [f"{k}={pretty(v)}" for k, v in kwargs.items()]
    return ", ".join(args + kwargs)
