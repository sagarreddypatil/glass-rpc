import logging
from enum import Enum
from .bidirpc import BidirPC, can_serialize

logger = logging.getLogger(__name__)


class RetType(Enum):
    VAL = 0
    REF = 1


class NetworkObj:
    """
    Stub for an object who's methods are executed on a remote
    """

    def __init__(self, rpc: BidirPC, obj_id):
        logger.info(f"netobj<{obj_id}> constructed")
        self.rpc = rpc
        self.obj_id = obj_id

    def __getattr__(self, name):
        if name in ("rpc", "obj_id"):
            return super().__getattr__(name)

        logger.info(f"netobj<{self.obj_id}>.__getattr__ {name}")
        ret = self.rpc.obj_getattr(self.obj_id, name)

        if ret[0] == RetType.VAL.value:
            return ret[1]
        elif ret[0] == RetType.REF.value:
            obj_id = ret[1]
            return NetworkObj(self.rpc, obj_id)

    def __call__(self, *args, **kwargs):
        logger.info(f"netobj<{self.obj_id}>.__call__ {args} {kwargs}")
        ret = self.rpc.obj_call(self.obj_id, args, kwargs)
        if ret[0] == RetType.VAL.value:
            return ret[1]
        elif ret[0] == RetType.REF.value:
            obj_id = ret[1]
            return NetworkObj(self.rpc, obj_id)

    def __del__(self):
        logger.info(f"netobj<{self.obj_id}>.__del__")
        self.rpc.obj_del(self.obj_id)


def obj_to_net(store, obj):
    if can_serialize(obj):
        return (RetType.VAL.value, obj)
    else:
        obj_id = id(obj)
        store[obj_id] = obj
        return (RetType.REF.value, obj_id)


def obj_from_net(rpc, net):
    typ = RetType(net[0])
    if typ == RetType.VAL:
        return net[1]
    elif typ == RetType.REF:
        obj_id = net[1]
        return NetworkObj(rpc, obj_id)


def add_network_obj_endpoints(rpc: BidirPC, store):
    @rpc.endpoint
    def obj_getattr(obj_id, name):
        obj = store[obj_id]
        logger.info(f"obj_getattr {obj} {name}")
        ret = store[obj_id].__getattribute__(name)
        return obj_to_net(store, ret)

    @rpc.endpoint
    def obj_call(obj_id, args, kwargs):
        obj = store[obj_id]
        logger.info(f"obj_call {obj} {args} {kwargs}")
        ret = store[obj_id].__call__(*args, **kwargs)
        return obj_to_net(store, ret)

    @rpc.endpoint
    def obj_del(obj_id):
        logger.info(f"obj_del {obj_id}")
        del store[obj_id]
