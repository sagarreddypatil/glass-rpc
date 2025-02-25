import sys
import types
import marshal
import importlib
from enum import Enum


class ObjType(Enum):
    SIMPLE = 0
    FUNC = 1
    REF = 10
    MOD_IMPORT = 11


def is_simple(obj):
    import msgpack

    try:
        msgpack.packb(obj)
        return True
    except Exception:
        return False


class FunctionDict(dict):
    def __init__(self, missing_func):
        self.missing_func = missing_func

    def __missing__(self, key):
        ret = self.missing_func(key)
        self[key] = ret
        return ret


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

    # def __del__(self):
    #     self.__glass_ser.rpc.obj_del(self.__glass_obj_id)


class Serializer:
    def __init__(self, rpc):
        self.rpc = rpc
        self.ref_objs = {}
        self.module_globals = FunctionDict(lambda mod: self.new_mod_globals(mod))

        @rpc.endpoint
        def add_obj(ser):
            typ = ObjType(ser[0])
            if typ == ObjType.SIMPLE:
                raise Exception(
                    "tried to capture simple object - you are probably doing something wrong"
                )
            elif typ == ObjType.REF:
                raise Exception("tried to capture a network reference object")

            obj = self.deserialize(ser)
            return self.serialize_ref(obj)

        @rpc.endpoint
        def obj_getattr(obj_id, name):
            obj = self.ref_objs[obj_id]
            attr = getattr(obj, name)
            return self.serialize(attr)

        @rpc.endpoint
        def obj_call(obj_id, args, kwargs):
            obj = self.ref_objs[obj_id]
            args = tuple(self.deserialize(arg) for arg in args)
            kwargs = {k: self.deserialize(v) for k, v in kwargs.items()}

            ret = obj(*args, **kwargs)
            return self.serialize(ret)

        @rpc.endpoint
        def obj_iter(obj_id):
            obj = self.ref_objs[obj_id]
            return self.serialize(iter(obj))

        @rpc.endpoint
        def obj_next(obj_id):
            obj = self.ref_objs[obj_id]
            return self.serialize(next(obj))

        # @rpc.endpoint
        # def obj_del(obj_id):
        #     del self.ref_objs[obj_id]

        @rpc.endpoint
        def get_global_endpoint(mod, name):
            assert mod == "__main__"
            main_globals = sys.modules["__main__"].__dict__
            obj = main_globals[name]

            return self.serialize(obj)

    def new_mod_globals(self, mod):
        out = FunctionDict(lambda name: self.get_global(mod, name))
        out["__name__"] = mod
        out["__builtins__"] = __builtins__
        return out

    def get_global(self, mod, name):
        if name in self.module_globals[mod]["__builtins__"]:
            return self.module_globals[mod]["__builtins__"][name]
        ser = self.rpc.get_global_endpoint(mod, name)
        return self.deserialize(ser)

    def serialize(self, obj):
        # if it's a trivially serializable, just send it
        if is_simple(obj):
            return [ObjType.SIMPLE.value, obj]

        if isinstance(obj, types.ModuleType):
            return [ObjType.MOD_IMPORT.value, obj.__name__, None]

        if (
            "__module__" in dir(obj)
            and "__name__" in dir(obj)
            and obj.__module__ != "__main__"
            and obj.__module__ is not None
        ):
            # import the module
            return [ObjType.MOD_IMPORT.value, obj.__module__, obj.__name__]

        # if it's a function, send the code
        if isinstance(obj, types.FunctionType):
            code_ser = marshal.dumps(obj.__code__)
            return [ObjType.FUNC.value, obj.__module__, obj.__name__, code_ser]

        # TODO: handle classes
        if isinstance(obj, type):
            raise Exception("unimplemented")

        # otherwise, send a reference
        return self.serialize_ref(obj)

    def serialize_ref(self, obj):
        obj_id = id(obj)
        self.ref_objs[obj_id] = obj
        return [ObjType.REF.value, obj_id]

    def deserialize(self, ser):
        typ = ObjType(ser[0])
        if typ == ObjType.SIMPLE:
            return ser[1]
        elif typ == ObjType.FUNC:
            mod, name, code_ser = ser[1:]
            code = marshal.loads(code_ser)
            func = types.FunctionType(code, self.module_globals[mod], name)
            return func
        elif typ == ObjType.REF:
            obj_id = ser[1]
            return NetworkObj(self, obj_id)
        elif typ == ObjType.MOD_IMPORT:
            mod, attr = ser[1:]
            mod = importlib.import_module(mod)
            if attr is None:
                return mod
            return getattr(mod, attr)

        raise Exception(f"unknown type {typ}")
