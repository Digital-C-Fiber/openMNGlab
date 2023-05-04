from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional, Type, Callable, TypeVar, Generic, Iterable
from unittest.mock import patch


def attrib_path(cls: Type, prop_name: str):
    return f"{cls.__module__}.{cls.__name__}.{prop_name}"


@dataclass
class Call:
    func: str
    args: tuple[Any]
    kwargs: dict[Any, Any]
    returned: Optional[Any] = None
    raised: Optional[Any] = None


@dataclass
class ObjectObserver:
    obj_id: int
    obj_type: Type
    calls: list[Call] = field(default_factory=list)

    def operation_called(self, name: str, *args, returned: Optional[Any] = None,
                         raised: Optional[Any] = None,
                         **kwargs):
        self.calls.append(Call(func=name, args=args, returned=returned, kwargs=kwargs, raised=raised))

    def get_calls(self, func: str | object) -> Iterable[Call]:
        func: str = func if isinstance(func, str) else func.__name__
        return (call for call in self.calls if call.func == func)


class PropertyWrapper:

    def __init__(self, observer: SpyObserver, orig_property: property, property_name: str):
        self._orig_name = property_name
        self._orig_property: property = orig_property
        self._observer = observer

    def __get__(self, instance: object, owner: Type):
        name = f"{instance.__class__.__name__}.{self._orig_name}.get"
        try:
            ret = self._orig_property.__get__(instance, owner)
            self._observer._operation_called(instance, name, returned=ret)
            return ret
        except BaseException as e:
            self._observer._operation_called(instance, name, raised=e)
            raise e

    def __set__(self, instance: object, value: Any):
        name = f"{instance.__class__.__name__}.{self._orig_name}.set"
        try:
            ret = self._orig_property.__set__(instance, value)
            self._observer._operation_called(instance, name, value)
            return ret
        except BaseException as e:
            self._observer._operation_called(instance, name, value, raised=e)
            raise e


KT = TypeVar("KT")
VT = TypeVar("VT")


class AtomicSetDict(dict[KT, VT], Generic[KT, VT]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = Lock()

    def get_or_set_if_new(self, key: KT, __new_value: Optional[VT] = None,
                          value_factory: Optional[Callable[[KT, ...], VT]] = None,
                          args: tuple = tuple(), **kwargs) -> VT:
        if __new_value is None and value_factory is None:
            raise ValueError("Must either set a value of a value factory")
        if key not in self:
            self._lock.acquire()
            try:
                if key not in self:
                    __new_value = value_factory(key, *args, **kwargs) if __new_value is None else __new_value
                    self[key] = __new_value
            finally:
                self._lock.release()
        return self[key]


class SpyObserver:
    def __init__(self, filter: bool = False):
        self._function_wrappers: AtomicSetDict[int, Callable] = AtomicSetDict()
        self.objects: AtomicSetDict[int, ObjectObserver] = AtomicSetDict()
        self.monitor_ids = set()
        self.filter = filter

    def get_calls_of(self, target_call: Callable, parent: Optional[Type] = None) -> Iterable[Call]:
        return (call for observer in self.objects.values() if
                     (parent is None or issubclass(observer.obj_type, parent)) for call in
                     observer.get_calls(target_call))

    @staticmethod
    def _object_observer_factory(obj_id: int, obj: object) -> ObjectObserver:
        return ObjectObserver(obj_id, type(obj))

    def _operation_called(self, calling_instance: object, name: str, *args, returned: Optional[Any] = None,
                          raised: Optional[Any] = None,
                          **kwargs):
        obj_id = id(calling_instance)
        if self.filter and obj_id not in self.monitor_ids:
            return
        self.objects.get_or_set_if_new(obj_id, value_factory=self._object_observer_factory,
                                       args=(calling_instance,)).operation_called(name, *args, returned=returned,
                                                                                  raised=raised, **kwargs)

    def _new_function_wrapper(self, actual_function: Callable, function_name: Optional[str] = None):
        function_name = function_name if function_name is not None else actual_function.__name__

        def spy_func_wrapper(patched_obj_self, *args, **kwargs):
            try:
                ret = actual_function(patched_obj_self, *args, **kwargs)
                self._operation_called(patched_obj_self, function_name, *args, **kwargs, returned=ret)
                return ret
            except BaseException as e:
                self._operation_called(patched_obj_self, function_name, *args, **kwargs, raised=e)
                raise e

        wrapper_instance = spy_func_wrapper
        wrapper_instance.__is_wrapped_by_omngl_spy = True
        return wrapper_instance

    def _function_wrapper(self, actual_function: Callable, function_name: Optional[str] = None) -> Callable:
        def new_func_wrapper(_, *args, **kwargs):
            return self._new_function_wrapper(*args, **kwargs)

        function_id = id(actual_function)
        return self._function_wrappers.get_or_set_if_new(function_id,
                                                         value_factory=new_func_wrapper, args=(actual_function,),
                                                         function_name=function_name)

    def patch_function(self, function) -> Any:
        if hasattr(function, "__is_wrapped_by_omngl_spy"):
            raise Exception("Refusing to patch an already patched function")
        return patch(f"{function.__module__}.{function.__qualname__}", new=self._function_wrapper(function))


def patch_property(obs, target_class, property_name):
    return patch(attrib_path(target_class, property_name),
                 new=PropertyWrapper(obs, target_class.__dict__[property_name], property_name))


def patch_method(obs, target_class, property_name):
    a = patch(attrib_path(target_class, property_name), new=patched_method(obs, target_class, property_name))
