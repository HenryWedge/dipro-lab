from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any, get_args, get_origin, get_type_hints


class WireCodec:
    def __init__(self):
        self._types = {}
        self._names = {}

    @classmethod
    def for_algorithm(cls, algorithm_type):
        codec = cls()
        for base in reversed(algorithm_type.__mro__):
            for method in vars(base).values():
                if not getattr(method, "__distributed_operation__", None):
                    continue
                try:
                    annotations = get_type_hints(method)
                except (NameError, TypeError):
                    annotations = getattr(method, "__annotations__", {})
                for name, value_type in annotations.items():
                    if name != "return":
                        codec._collect_type(value_type)
                codec._collect_type(annotations.get("return", type(None)))
        return codec

    def _collect_type(self, value_type):
        if (value_type is Any
            or value_type is None
            or value_type is type(None)
            or self._collect_generic_arguments(value_type)
            or self._is_builtin_or_already_collected(value_type)
        ):
            return
        name = f"{value_type.__module__}.{value_type.__qualname__}"
        if is_dataclass(value_type):
            self._register_dataclass(value_type, name)
            return
        elif self._register_wire_type(value_type, name):
            return
        raise TypeError(
            f"operation type {value_type.__module__}.{value_type.__qualname__} "
            "must define to_wire() and from_wire()"
        )

    def _collect_generic_arguments(self, value_type):
        if get_origin(value_type) is None:
            return False
        for member_type in get_args(value_type):
            self._collect_type(member_type)
        return True

    def _is_builtin_or_already_collected(self, value_type):
        return (
            not isinstance(value_type, type)
            or value_type in (str, int, float, bool, dict, list, datetime, type(None))
            or value_type in self._types
        )

    def _register_dataclass(self, value_type, name):
        self._types[value_type] = name
        self._names[name] = value_type
        for field in fields(value_type):
            self._collect_type(field.type)

    def _register_wire_type(self, value_type, name):
        if not (
            callable(getattr(value_type, "to_wire", None))
            and callable(getattr(value_type, "from_wire", None))
        ):
            return False
        self._types[value_type] = name
        self._names[name] = value_type
        return True

    def encode(self, value):
        if isinstance(value, datetime):
            return {"__type__": "datetime", "value": value.isoformat()}
        if isinstance(value, dict):
            return {key: self.encode(item) for key, item in value.items()}
        if isinstance(value, list) or isinstance(value, set):
            return [self.encode(item) for item in value]
        for value_type, name in self._types.items():
            if isinstance(value, value_type):
                wire_value = (
                    {field.name: getattr(value, field.name) for field in fields(value)}
                    if is_dataclass(value)
                    else value.to_wire()
                )
                return {"__type__": name, "value": self.encode(wire_value)}
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise TypeError(f"value of type {type(value).__name__} is not wire-serializable")

    def decode(self, value):
        if isinstance(value, list):
            return [self.decode(item) for item in value]
        if not isinstance(value, dict):
            return value
        object_type = value.get("__type__")
        if object_type == "datetime":
            return datetime.fromisoformat(value["value"])
        value_type = self._names.get(object_type)
        if value_type is not None:
            decoded_value = self.decode(value["value"])
            if is_dataclass(value_type):
                return value_type(**decoded_value)
            return value_type.from_wire(decoded_value)
        return {key: self.decode(item) for key, item in value.items()}
