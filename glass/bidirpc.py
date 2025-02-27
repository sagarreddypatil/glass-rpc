import socket
import logging
from enum import Enum
import msgpack
import pickle
from tblib import pickling_support
from .util import fmt_args_kwargs, pretty
import json


class BytesEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return f"<bytes {len(o)}>"
        else:
            return super().default(o)


pickling_support.install()

logger = logging.getLogger(__name__)


class ReqType(Enum):
    CALL = 0
    RET = 1
    ERR = 2


def can_serialize(obj):
    try:
        msgpack.packb(obj)
        return True
    except Exception:
        return False


class BidirPC:
    """
    Bidirectional RPC handler, based on a socket connection.
    The socket connection can be either the client or server side.
    """

    def __init__(self):
        self.endpoints = {}
        self.unpacker = msgpack.Unpacker()
        self.queue = []
        self.conn = None

    def endpoint(self, func):
        self.endpoints[func.__name__] = func
        return func

    def live(self):
        if self.conn:
            return self.conn.fileno() != -1
        return False

    def connect(self, conn):
        assert self.conn is None
        assert isinstance(conn, socket.socket)
        self.conn = conn
        return self

    def recv(self):
        while len(self.queue) == 0:
            resp = self.conn.recv(1024)
            if not resp:
                raise EOFError

            self.unpacker.feed(resp)
            for req in self.unpacker:
                req_type = ReqType(req[0])
                req = req[1:]
                if req_type == ReqType.CALL:
                    cmd, args, kwargs = req
                    resp = self.endpoints[cmd](*args, **kwargs)
                    resp = (ReqType.RET.value, resp)
                    self.conn.send(msgpack.packb(resp))
                elif req_type == ReqType.RET:
                    ret = req[0]
                    self.queue.append(ret)
                elif req_type == ReqType.ERR:
                    s = req[0]
                    exc = pickle.loads(s)
                    raise exc

        return self.queue.pop(0)

    def exception(self, exc):
        try:
            raise exc
        except KeyError as e:
            raise e
        except Exception:
            pass

        s = pickle.dumps(exc)
        self.conn.send(msgpack.packb([ReqType.ERR.value, s]))

    def __getattr__(self, name):
        def call(*args, **kwargs):
            packet = (ReqType.CALL.value, name, args, kwargs)
            packet = msgpack.packb(packet)
            self.conn.send(packet)
            resp = self.recv()
            logger.debug(f"{name} -> ({fmt_args_kwargs(args, kwargs)}) -> {pretty(resp)}")
            return resp

        return call
