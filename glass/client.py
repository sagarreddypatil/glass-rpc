import types
import socket
import marshal
import msgpack
from .bidirpc import BidirPC


class Connection(BidirPC):
    def __init__(self, host, port):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.connect(self.socket)

    def close(self):
        self.socket.close()


EXCLUDE_GLOBALS = {
    # "__name__",
    "__doc__",
    "__package__",
    "__loader__",
    "__spec__",
    "__annotations__",
    "__builtins__",
    "__file__",
    "__cached__",
    # "os",
    # "getcwd",
    # "Remote",
    # "remote",
    # "cwd_info",
    # "print_host",
    # "main",
}


class Remote:
    def __init__(self, host, port):
        self.conn = Connection(host, port)
        self.synced_globals = set()

    def func(self, func: types.FunctionType):
        if func.__closure__ is not None:
            raise Exception("Cannot handle closures")

        names = set(func.__code__.co_names)

        def new_func(*args, **kwargs):
            unsynced_globals = names.intersection(
                set(func.__globals__.keys()) - self.synced_globals - EXCLUDE_GLOBALS
            )

            for gn in unsynced_globals:
                val = func.__globals__[gn]
                if isinstance(val, types.ModuleType):  # need to import module
                    self.conn.add_global_import(gn, val.__name__)
                elif "__module__" not in dir(val):  # arbitrary object
                    raise Exception(f"Cannot handle global {gn}")
                elif "__name__" not in dir(val):  # built-in object?
                    raise Exception(f"Cannot handle global {gn}")
                elif val.__module__ != func.__module__:  # need to import member
                    self.conn.add_global_import(gn, val.__module__, val.__name__)
                else:  # same level as this function, transfer it
                    self.conn.add_global_func(gn, marshal.dumps(val.__code__))

            return self.conn.call_name(func.__name__, args, kwargs)

        self.conn.add_global_func(func.__name__, marshal.dumps(func.__code__))
        return new_func
