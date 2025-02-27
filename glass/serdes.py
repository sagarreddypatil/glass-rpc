import re
import sys
import types
import inspect
import marshal
import importlib
import logging
from .types import ObjType
from .netobj import NetworkObj, netobj_endpoints

# Get logger for this module
logger = logging.getLogger(__name__)


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
        if ret is None:
            super().__missing__(key)
        self[key] = ret
        return ret


class Serializer:
    def __init__(self, rpc):
        logger.debug("initializing serializer")
        self.rpc = rpc
        self.ref_objs = {}
        self.module_globals = FunctionDict(lambda mod: self.new_mod_globals(mod))
        netobj_endpoints(self, rpc)

        @rpc.endpoint
        def get_global_endpoint(mod, name):
            assert mod == "__main__"
            main_globals = sys.modules["__main__"].__dict__
            obj = main_globals[name]

            return self.serialize_ref(obj)

    def new_mod_globals(self, mod):
        logger.debug(f"creating new module globals: {mod}")
        out = FunctionDict(lambda name: self.get_global(mod, name))
        out["__name__"] = mod
        return out

    def get_global(self, mod, name):
        logger.debug(f"get_global: {mod}.{name}")
        if name in __builtins__:
            logger.debug(f"found in builtins: {name}")
            return __builtins__[name]
        ser = self.rpc.get_global_endpoint(mod, name)
        logger.debug(f"retrieved via rpc: {name}")
        return self.deserialize(ser)

    def serialize(self, obj, context=[]):
        if obj in context:
            # circular reference
            raise Exception(f"circular reference {context} -> {obj}")

        # if it's a trivially serializable, just send it
        if is_simple(obj):
            logger.debug(f"serialize: simple object {type(obj).__name__}")
            return [ObjType.SIMPLE.value, obj]

        if isinstance(obj, types.CellType):
            logger.debug(f"serialize: cell {obj}")
            if obj.cell_contents in context:
                return [ObjType.CELL_REF.value, id(obj.cell_contents)]
            else:
                return [ObjType.CELL_DIRECT.value, self.serialize(obj.cell_contents)]

        if isinstance(obj, types.ModuleType):
            logger.debug(f"serialize: module {obj.__name__}")
            return [ObjType.MOD_IMPORT.value, obj.__name__, None]

        try:
            if obj.__module__ != "__main__" and obj.__module__ is not None:
                # import the module
                logger.debug(f"serialize: module member {obj.__module__}.{obj.__name__}")
                return [ObjType.MOD_IMPORT.value, obj.__module__, obj.__name__]
        except AttributeError:
            pass

        # if it's a function, send the code
        if isinstance(obj, types.FunctionType):
            logger.debug(f"serialize: function {obj.__module__}.{obj.__qualname__}")
            code_ser = marshal.dumps(obj.__code__)
            argdefs_ser = self.serialize(obj.__defaults__, context + [obj])
            kwdefs_ser = self.serialize(obj.__kwdefaults__, context + [obj])
            if obj.__closure__ is None:
                closure_ser = None
            else:
                closure_ser = tuple(self.serialize(c, context + [obj]) for c in obj.__closure__)
            return [
                ObjType.FUNC.value,
                obj.__module__,
                obj.__name__,
                argdefs_ser,
                kwdefs_ser,
                code_ser,
                closure_ser,
            ]

        if isinstance(obj, type):
            context = context + [obj]
            name = obj.__name__
            bases = obj.__bases__
            bases_ser = tuple(self.serialize(b, context) for b in bases)

            dict_exclude = {"__dict__", "__weakref__", "__doc__"}
            objdict = obj.__dict__
            dict_ser = {
                k: self.serialize(v, context) for k, v in objdict.items() if k not in dict_exclude
            }
            return [ObjType.CLS.value, id(obj), name, bases_ser, dict_ser]

        # otherwise, send a reference
        logger.debug(f"serialize: reference {type(obj).__name__}")
        return self.serialize_ref(obj)

    def serialize_ref(self, obj):
        obj_id = id(obj)
        logger.debug(f"serialize_ref: {type(obj).__name__} id={obj_id}")
        self.ref_objs[obj_id] = obj
        return [ObjType.REF.value, obj_id]

    def deserialize(self, ser):
        typ = ObjType(ser[0])
        if typ == ObjType.SIMPLE:
            logger.debug(f"deserialize: {typ}")
            return ser[1]
        elif typ == ObjType.FUNC:
            mod, name, argdefs_ser, kwdefs_ser, code_ser, closure_ser = ser[1:]
            logger.debug(f"deserialize: {typ} {mod}.{name}")
            code = marshal.loads(code_ser)
            if closure_ser is None:
                closure = None
            else:
                closure = tuple(self.deserialize(c) for c in closure_ser)
            if argdefs_ser is None:
                argdefs = None
            else:
                argdefs = tuple(self.deserialize(argdefs_ser))
            if kwdefs_ser is None:
                kwdefs = None
            else:
                kwdefs = self.deserialize(kwdefs_ser)
            func = types.FunctionType(
                code, self.module_globals[mod], name, argdefs, closure, kwdefs
            )
            return func
        elif typ == ObjType.CLS:
            old_id, name, bases_ser, dict_ser = ser[1:]
            self.placeholders = {}
            logger.debug(f"deserialize: {typ} {name}")
            bases = tuple(self.deserialize(b) for b in bases_ser)
            objdict = {k: self.deserialize(v) for k, v in dict_ser.items()}
            cls = type(name, bases, objdict)
            if old_id in self.placeholders:
                cell: types.CellType = self.placeholders[old_id]
                cell.cell_contents = cls
            return cls
        elif typ == ObjType.CELL_REF:
            cell = types.CellType(object())
            self.placeholders[ser[1]] = cell
            return cell
        elif typ == ObjType.CELL_DIRECT:
            return types.CellType(self.deserialize(ser[1]))
        elif typ == ObjType.REF:
            obj_id = ser[1]
            return NetworkObj(self, obj_id)
        elif typ == ObjType.MOD_IMPORT:
            mod, attr = ser[1:]
            if attr is None:
                logger.debug(f"deserialize: {typ} module={mod}")
            else:
                logger.debug(f"deserialize: {typ} {mod}.{attr}")
            mod = importlib.import_module(mod)
            if attr is None:
                return mod
            return getattr(mod, attr)

        raise Exception(f"unknown type {typ}")
