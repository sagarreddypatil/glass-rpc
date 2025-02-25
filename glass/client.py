import socket
from .serdes import Serializer
from .bidirpc import BidirPC


class Remote:
    def __init__(self, host, port):
        self.conn = socket.create_connection((host, port))

        self.rpc = BidirPC()
        self.rpc.connect(self.conn)

        self.ser = Serializer(self.rpc)

    def capture(self, obj):
        ser = self.ser.serialize(obj)
        stub = self.rpc.add_obj(ser)
        stub = self.ser.deserialize(stub)
        return stub
