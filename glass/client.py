import sys
import socket
from .serdes import Serializer
from .bidirpc import BidirPC
import logging

# logging.basicConfig(
#     level=logging.DEBUG,
#     format="[%(levelname)s][%(process)d] %(asctime)s %(name)s: %(message)s",
# )
# logger = logging.getLogger(__name__)


class Remote:
    def __init__(self, host, port):
        self.conn = socket.create_connection((host, port))

        self.rpc = BidirPC()
        self.rpc.connect(self.conn)

        self.ser = Serializer(self.rpc)

    def capture(self, obj):
        # raise exception if obj is a method in a class
        if hasattr(obj, "__qualname__") and "." in obj.__qualname__:
            raise Exception("cannot capture bound method")

        ser = self.ser.serialize(obj)
        stub = self.rpc.add_obj(ser, to_global=True)
        stub = self.ser.deserialize(stub)
        return stub
