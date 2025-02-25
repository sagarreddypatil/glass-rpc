import os
import types
import socket
import marshal
import msgpack
import importlib


class Server:
    def __init__(self):
        self.commands = {}

    def run(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)

        while True:
            conn, _addr = s.accept()
            pid = os.fork()
            if pid == 0:
                unpacker = msgpack.Unpacker()
                while True:
                    resp = conn.recv(1024)
                    if not resp:
                        break
                    unpacker.feed(resp)
                    for req in unpacker:
                        resp = self.process_request(req)
                        conn.send(msgpack.packb(resp))
                conn.close()
                os._exit(0)
            else:
                conn.close()

    def process_request(self, req):
        cmd = req["cmd"]
        args = req["args"]
        kwargs = req["kwargs"]

        resp = self.commands[cmd](*args, **kwargs)
        return resp

    def command(self, func):
        self.commands[func.__name__] = func
        return func


server = Server()
glbls = {"__name__": "__remote__"}


@server.command
def add_global_func(name, code):
    code = marshal.loads(code)
    func = types.FunctionType(code, glbls, name)
    glbls[name] = func


@server.command
def call_name(name, args, kwargs):
    return glbls[name](*args, **kwargs)


@server.command
def add_global_import(name, module, member=None):
    item = importlib.import_module(module)
    if member:
        item = getattr(item, member)
    glbls[name] = item


if __name__ == "__main__":
    server.run("localhost", 8000)
