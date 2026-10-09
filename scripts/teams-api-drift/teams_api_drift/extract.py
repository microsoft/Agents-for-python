# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Run inside an isolated upstream environment; never instantiate API clients."""

import ast
import enum
import importlib
from importlib import metadata
import inspect
import json
import pkgutil
import platform
import re
import sys
import textwrap
import types
import typing

from pydantic import BaseModel, TypeAdapter

from . import EXTRACTOR_VERSION
from .common import DEPENDENCY, write_json


def qualified(value):
    return f"{value.__module__}.{value.__qualname__}"


def type_name(value):
    if value is inspect.Signature.empty:
        return "Any"
    if value is None or value is type(None):
        return "None"
    if isinstance(value, (str, typing.ForwardRef)):
        return str(
            value.__forward_arg__ if isinstance(value, typing.ForwardRef) else value
        )
    origin = typing.get_origin(value)
    args = typing.get_args(value)
    if origin is typing.Annotated:
        metadata_text = json.dumps([stable(item) for item in args[1:]], sort_keys=True)
        return f"Annotated[{type_name(args[0])}, {metadata_text}]"
    if origin is typing.Literal:
        return (
            "Literal["
            + ", ".join(
                sorted(json.dumps(stable(item), sort_keys=True) for item in args)
            )
            + "]"
        )
    if origin in (typing.Union, types.UnionType):
        return " | ".join(sorted(type_name(arg) for arg in args))
    if origin:
        return f"{type_name(origin)}[{', '.join(type_name(arg) for arg in args)}]"
    if isinstance(value, type):
        return (
            value.__qualname__ if value.__module__ == "builtins" else qualified(value)
        )
    if isinstance(value, TypeAdapter):
        return f"TypeAdapter[{type_name(value._type)}]"
    if isinstance(value, list):
        return "[" + ", ".join(type_name(item) for item in value) + "]"
    if hasattr(value, "__value__") and hasattr(value, "__type_params__"):
        return type_name(value.__value__)
    if callable(value) and hasattr(value, "__qualname__"):
        return qualified(value)
    return re.sub(r"\btyping\.", "", str(value))


def stable(value):
    """Represent defaults/config without repr addresses or host paths."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, enum.Enum):
        return {"enum": qualified(type(value)), "value": stable(value.value)}
    if isinstance(value, dict):
        return {
            str(k): stable(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        }
    if isinstance(value, (list, tuple)):
        return [stable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(
            (stable(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True)
        )
    if callable(value) and hasattr(value, "__qualname__"):
        return {"callable": qualified(value)}
    if hasattr(value, "convert_to_aliases"):
        return value.convert_to_aliases()
    # PydanticUndefined and metadata such as annotated_types.Ge/MaxLen.
    attributes = getattr(value, "__dict__", None)
    slots = getattr(type(value), "__slots__", ())
    if attributes or slots:
        return {
            "type": qualified(type(value)),
            "attributes": stable(
                attributes or {k: getattr(value, k) for k in slots if hasattr(value, k)}
            ),
        }
    return {"type": qualified(type(value))}


def hints(value):
    try:
        return typing.get_type_hints(value, include_extras=True)
    except (NameError, TypeError):
        # TYPE_CHECKING-only imports need not exist at runtime. Keep their annotation.
        return getattr(value, "__annotations__", {})


def signature(value, drop_self=False):
    sig = inspect.signature(value)
    annotations = hints(value)
    parameters = []
    for parameter in sig.parameters.values():
        if drop_self and parameter.name in ("self", "cls"):
            continue
        parameters.append(
            {
                "name": parameter.name,
                "kind": parameter.kind.name,
                "optional": parameter.default is not inspect.Signature.empty,
                "default": stable(parameter.default),
                "type": type_name(
                    annotations.get(parameter.name, parameter.annotation)
                ),
            }
        )
    return {
        "parameters": parameters,
        "returnType": type_name(annotations.get("return", sig.return_annotation)),
        "async": inspect.iscoroutinefunction(value),
    }


def signatures(value, drop_self=False):
    overloads = typing.get_overloads(value)
    return [signature(overload, drop_self) for overload in overloads or [value]]


def instance_properties(cls):
    properties = {}
    for base in reversed(cls.__mro__):
        if not base.__module__.startswith("microsoft_teams."):
            continue
        initializer = base.__dict__.get("__init__")
        if not initializer or not inspect.isfunction(initializer):
            continue
        for name, annotation in hints(base).items():
            if not name.startswith("_"):
                properties[name] = {
                    "type": type_name(annotation),
                    "optional": hasattr(base, name),
                }
        if initializer.__code__.co_filename.startswith("<"):
            # Dataclass-generated initializers have no source. Their fields are
            # represented by annotations and their generated callable signature.
            continue
        tree = ast.parse(textwrap.dedent(inspect.getsource(initializer)))
        annotations = hints(initializer)
        for node in ast.walk(tree):
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else ([node.target] if isinstance(node, ast.AnnAssign) else [])
            )
            for target in targets:
                if not (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and not target.attr.startswith("_")
                ):
                    continue
                value = node.value
                annotation = "Any"
                if isinstance(node, ast.AnnAssign):
                    annotation = ast.unparse(node.annotation)
                elif isinstance(value, ast.Name):
                    annotation = type_name(annotations.get(value.id, typing.Any))
                elif isinstance(value, ast.Constant):
                    annotation = type_name(type(value.value))
                elif isinstance(value, ast.Call):
                    if isinstance(value.func, ast.Name):
                        called = initializer.__globals__.get(value.func.id)
                        annotation = (
                            type_name(called) if isinstance(called, type) else "Any"
                        )
                    elif isinstance(value.func, ast.Attribute) and isinstance(
                        value.func.value, ast.Name
                    ):
                        annotation = type_name(
                            annotations.get(value.func.value.id, typing.Any)
                        )
                properties[target.attr] = {"type": annotation, "optional": False}
    return properties


def model_for(value, name):
    result = {
        "name": name,
        "kind": "type",
        "properties": {},
        "methods": {},
        "constructors": [],
        "enumMembers": {},
        "exportPaths": [],
        "deprecated": bool(getattr(value, "__deprecated__", False)),
    }
    if inspect.isclass(value):
        result["kind"] = "class"
        result["properties"].update(instance_properties(value))
        if issubclass(value, BaseModel):
            result["kind"] = "model"
            result["modelConfig"] = stable(value.model_config)
            for field_name, field in value.model_fields.items():
                result["properties"][field_name] = {
                    "type": type_name(field.annotation),
                    "optional": not field.is_required(),
                    "default": stable(field.default),
                    "defaultFactory": stable(field.default_factory),
                    "alias": stable(field.alias),
                    "validationAlias": stable(field.validation_alias),
                    "serializationAlias": stable(field.serialization_alias),
                    "metadata": stable(field.metadata),
                    "exclude": stable(field.exclude),
                    "frozen": stable(field.frozen),
                    "discriminator": stable(field.discriminator),
                }
        elif issubclass(value, enum.Enum):
            result["kind"] = "enum"
            result["enumMembers"] = {
                key: stable(member.value) for key, member in value.__members__.items()
            }
        else:
            initializer = value.__init__
            if inspect.isfunction(initializer):
                result["constructors"] = signatures(initializer, True)
        for base in reversed(value.__mro__):
            if not base.__module__.startswith("microsoft_teams."):
                continue
            for member, descriptor in vars(base).items():
                if member.startswith("_"):
                    continue
                if isinstance(descriptor, property):
                    result["properties"][member] = {
                        "type": type_name(
                            hints(descriptor.fget).get("return", typing.Any)
                        ),
                        "optional": False,
                        "writable": descriptor.fset is not None,
                        "deprecated": bool(
                            getattr(descriptor.fget, "__deprecated__", False)
                        ),
                    }
                else:
                    method = (
                        descriptor.__func__
                        if isinstance(descriptor, (staticmethod, classmethod))
                        else descriptor
                    )
                    if inspect.isfunction(method):
                        result["methods"][member] = signatures(method, True)
    elif inspect.isfunction(value):
        result["kind"] = "function"
        result["methods"]["$call"] = signatures(value)
    else:
        result["type"] = type_name(value)
        if isinstance(value, (str, int, float, bool)):
            result["value"] = stable(value)
    return result


def extract(package_name="microsoft_teams.api"):
    package = importlib.import_module(package_name)
    names = [package_name] + sorted(
        m.name
        for m in pkgutil.walk_packages(package.__path__, package_name + ".")
        if not any(part.startswith("_") for part in m.name.split("."))
    )
    symbols = {}
    for module_name in names:
        module = importlib.import_module(module_name)
        exports = getattr(module, "__all__", None)
        if exports is None:
            exports = [
                name
                for name, value in vars(module).items()
                if not name.startswith("_")
                and getattr(value, "__module__", "") == module_name
            ]
        for export in sorted(exports):
            value = getattr(module, export)  # Invalid __all__ must fail extraction.
            if inspect.ismodule(value):
                continue
            if inspect.isclass(value) or inspect.isfunction(value):
                name = qualified(value)
            else:
                name = f"{module_name}.{export}"
            if name not in symbols:
                try:
                    symbols[name] = model_for(value, name)
                except Exception as error:
                    raise ValueError(f"Unable to extract {name}: {error}") from error
            symbols[name]["exportPaths"].append(f"{module_name}.{export}")
    if not symbols:
        raise ValueError("No public API symbols extracted")
    for symbol in symbols.values():
        symbol["exportPaths"] = sorted(set(symbol["exportPaths"]))
    return {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "version": metadata.version(DEPENDENCY),
        "extractorVersion": EXTRACTOR_VERSION,
        "pythonVersion": platform.python_version(),
        "resolvedDependencies": dict(
            sorted((d.metadata["Name"], d.version) for d in metadata.distributions())
        ),
        "symbols": sorted(symbols.values(), key=lambda s: s["name"]),
    }


if __name__ == "__main__":
    write_json(sys.argv[1], extract())
