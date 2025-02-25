import os
import types
import socket
import marshal
import importlib
from .bidirpc import BidirPC

rpc = BidirPC()
glbls = {"__name__": "__remote__"}


@rpc.endpoint
def add_global_func(name, code):
    code = marshal.loads(code)
    func = types.FunctionType(code, glbls, name)
    glbls[name] = func


@rpc.endpoint
def call_name(name, args, kwargs):
    return glbls[name](*args, **kwargs)


@rpc.endpoint
def add_global_import(name, module, member=None):
    item = importlib.import_module(module)
    if member:
        item = getattr(item, member)
    glbls[name] = item


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: server.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    while True:
        conn, _addr = s.accept()
        pid = os.fork()
        if pid == 0:
            rpc.connect(conn)
            while True:
                try:
                    rpc.recv()
                except EOFError:
                    print("connection closed")
                    break
                except Exception as e:
                    rpc.exception(e)

            conn.close()
            os._exit(0)
        else:
            conn.close()
