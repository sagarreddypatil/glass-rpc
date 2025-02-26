import json

class BytesEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return f"<bytes {len(o)}>"
        else:
            return super().default(o)

def pretty(s):
    return json.dumps(s, cls=BytesEncoder)


def fmt_args_kwargs(args, kwargs):
    args = [f"{pretty(arg)}" for arg in args]
    kwargs = [f"{k}={pretty(v)}" for k, v in kwargs.items()]
    return ", ".join(args + kwargs)
