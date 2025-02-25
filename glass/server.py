import os
import types
import socket
import marshal
import logging
import importlib
from .network_obj import obj_to_net, obj_from_net, add_network_obj_endpoints
from .bidirpc import BidirPC

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(process)d] %(asctime)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


rpc = BidirPC()
glbls = {"__name__": "__remote__"}
objs = {}


@rpc.endpoint
def add_global_func(name, code):
    logger.info(f"add_global_func {name}")
    code = marshal.loads(code)
    func = types.FunctionType(code, glbls, name)
    glbls[name] = func


@rpc.endpoint
def add_global_import(name, module, member=None):
    logger.info(f"from {module} import {member if member else '*'} as {name}")
    item = importlib.import_module(module)
    if member:
        item = getattr(item, member)
    glbls[name] = item


@rpc.endpoint
def call_name(name, args, kwargs):
    args = tuple(obj_from_net(rpc, arg) for arg in args)
    kwargs = {k: obj_from_net(rpc, v) for k, v in kwargs.items()}

    logger.info(f"call_name {name} {args} {kwargs}")
    ret = glbls[name](*args, **kwargs)
    return obj_to_net(objs, ret)


add_network_obj_endpoints(rpc, objs)


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
        conn, addr = s.accept()
        pid = os.fork()
        if pid == 0:
            pid = os.getpid()
            logger.info(f"connection accepted from {addr}")
            rpc.connect(conn)
            while True:
                try:
                    rpc.recv()
                except EOFError:
                    logger.info("connection closed")
                    break
                except Exception as e:
                    rpc.exception(e)

            conn.close()
            os._exit(0)
        else:
            conn.close()
