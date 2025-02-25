import sys
import types
import marshal
import importlib
from .types import ObjType
from .netobj import NetworkObj, netobj_endpoints


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


class Serializer:
    def __init__(self, rpc):
        self.rpc = rpc
        self.ref_objs = {}
        self.module_globals = FunctionDict(lambda mod: self.new_mod_globals(mod))
        netobj_endpoints(self, rpc)

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
            if obj.__closure__ is None:
                closure_ser = None
            else:
                closure_ser = tuple(self.serialize_ref(c.cell_contents) for c in obj.__closure__)
            return [ObjType.FUNC.value, obj.__module__, obj.__name__, code_ser, closure_ser]

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
            mod, name, code_ser, closure_ser = ser[1:]
            code = marshal.loads(code_ser)
            if closure_ser is None:
                closure = None
            else:
                closure = tuple(types.CellType(self.deserialize(c)) for c in closure_ser)
            func = types.FunctionType(code, self.module_globals[mod], name, None, closure)
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
