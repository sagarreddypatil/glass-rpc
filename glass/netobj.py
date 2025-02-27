from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .serdes import Serializer
from .types import ObjType


class NetworkObj:
    def __init__(self, ser, obj_id):
        self.__glass_ser = ser
        self.__glass_obj_id = obj_id

    def __getattr__(self, name):
        if name.startswith("__glass_"):
            return super().__getattr__(name)

        ser = self.__glass_ser.rpc.obj_getattr(self.__glass_obj_id, name)
        return self.__glass_ser.deserialize(ser)

    def __call__(self, *args, **kwargs):
        args = tuple(self.__glass_ser.serialize(arg) for arg in args)
        kwargs = {k: self.__glass_ser.serialize(v) for k, v in kwargs.items()}

        ser = self.__glass_ser.rpc.obj_call(self.__glass_obj_id, args, kwargs)
        return self.__glass_ser.deserialize(ser)

    def __iter__(self):
        ser = self.__glass_ser.rpc.obj_iter(self.__glass_obj_id)
        return self.__glass_ser.deserialize(ser)

    def __next__(self):
        ser = self.__glass_ser.rpc.obj_next(self.__glass_obj_id)
        return self.__glass_ser.deserialize(ser)

    def __del__(self):
        rpc = self.__glass_ser.rpc
        if not rpc.live():
            return

        rpc.obj_del(self.__glass_obj_id)


# class NetworkCell(types


def netobj_endpoints(srl: "Serializer", rpc):
    @rpc.endpoint
    def add_obj(ser, to_global=False):
        typ = ObjType(ser[0])
        if typ == ObjType.SIMPLE:
            raise Exception(
                "tried to capture simple object - you are probably doing something wrong"
            )
        elif typ == ObjType.REF:
            raise Exception("tried to capture a network reference object")

        obj = srl.deserialize(ser)
        if to_global:
            srl.module_globals[obj.__module__][obj.__name__] = obj
        return srl.serialize_ref(obj)

    @rpc.endpoint
    def obj_getattr(obj_id, name):
        obj = srl.ref_objs[obj_id]
        attr = getattr(obj, name)
        return srl.serialize(attr)

    @rpc.endpoint
    def obj_call(obj_id, args, kwargs):
        obj = srl.ref_objs[obj_id]
        args = tuple(srl.deserialize(arg) for arg in args)
        kwargs = {k: srl.deserialize(v) for k, v in kwargs.items()}

        ret = obj(*args, **kwargs)
        return srl.serialize(ret)

    @rpc.endpoint
    def obj_iter(obj_id):
        obj = srl.ref_objs[obj_id]
        return srl.serialize(iter(obj))

    @rpc.endpoint
    def obj_next(obj_id):
        obj = srl.ref_objs[obj_id]
        return srl.serialize(next(obj))

    @rpc.endpoint
    def obj_iadd(obj_id, other):
        other = srl.deserialize(other)
        obj = srl.ref_objs[obj_id]
        obj += other
        return srl.serialize(obj)

    @rpc.endpoint
    def obj_del(obj_id):
        if obj_id not in srl.ref_objs:
            logger.debug(f"obj_del: {obj_id} not found")
            return
        del srl.ref_objs[obj_id]
