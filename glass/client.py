import types
import socket
import marshal

from .bidirpc import BidirPC
from .network_obj import obj_to_net, obj_from_net, add_network_obj_endpoints


class Connection(BidirPC):
    def __init__(self, host, port):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.connect(self.socket)

        self.objs = {}
        add_network_obj_endpoints(self, self.objs)

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

    def sync_globals(self, items, parent_mod=None):
        for gn, val in items.items():
            if gn in EXCLUDE_GLOBALS or gn in self.synced_globals:
                continue
            if isinstance(val, types.ModuleType):  # need to import module
                self.conn.add_global_import(gn, val.__name__)
            elif "__module__" not in dir(val):  # arbitrary object
                raise Exception(f"Cannot handle global {gn}")
            elif "__name__" not in dir(val):  # built-in object?
                raise Exception(f"Cannot handle global {gn}")
            elif val.__module__ != parent_mod:  # need to import member
                self.conn.add_global_import(gn, val.__module__, val.__name__)
            elif isinstance(val, types.FunctionType):  # at same level as this function, send it
                self.func(val)
            else:
                raise Exception(f"Cannot handle global {gn}")


    def func(self, func: types.FunctionType):
        if func.__closure__ is not None:
            raise Exception("Cannot handle closures")

        names = set(func.__code__.co_names)
        unsynced_globals = names.intersection(set(func.__globals__.keys()))
        unsynced_globals = {gn: func.__globals__[gn] for gn in unsynced_globals}
        self.sync_globals(unsynced_globals, func.__module__)

        def new_func(*args, **kwargs):
            unsynced_globals = names.intersection(set(func.__globals__.keys()))
            unsynced_globals = {gn: func.__globals__[gn] for gn in unsynced_globals}
            self.sync_globals(unsynced_globals, func.__module__)

            args = tuple(obj_to_net(self.conn.objs, arg) for arg in args)
            kwargs = {k: obj_to_net(self.conn.objs, v) for k, v in kwargs.items()}

            ret = self.conn.call_name(func.__name__, args, kwargs)
            return obj_from_net(self.conn, ret)

        self.conn.add_global_func(func.__name__, marshal.dumps(func.__code__))
        return new_func
