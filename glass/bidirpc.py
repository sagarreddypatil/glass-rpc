import sys
import logging
import traceback
from enum import Enum
import msgpack

logger = logging.getLogger(__name__)


class ReqType(Enum):
    CALL = 0
    RET = 1
    ERR = 2


class RemoteError(Exception):
    pass


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

    def connect(self, conn):
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
                    logger.debug(
                        f"endpoint {cmd} {len(args)} args, {len(kwargs)} kwargs"
                    )
                    resp = self.endpoints[cmd](*args, **kwargs)
                    resp = (ReqType.RET.value, resp)
                    self.conn.send(msgpack.packb(resp))
                elif req_type == ReqType.RET:
                    ret = req[0]
                    logger.debug(f"ret {ret}")
                    self.queue.append(ret)
                elif req_type == ReqType.ERR:
                    msg, tb = req
                    print(
                        f"=== Error in remote ===\n{tb}=== End Remote Error ===",
                        file=sys.stderr,
                    )
                    raise RemoteError(msg)

        return self.queue.pop(0)

    def exception(self, err):
        msg = str(err)
        tb = traceback.format_exc()

        self.conn.send(
            msgpack.packb(
                (
                    ReqType.ERR.value,
                    msg,
                    tb,
                )
            )
        )

    def __getattr__(self, name):
        def call(*args, **kwargs):
            packet = (ReqType.CALL.value, name, args, kwargs)
            packet = msgpack.packb(packet)
            self.conn.send(packet)
            return self.recv()

        return call
