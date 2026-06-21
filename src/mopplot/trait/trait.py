# created by lesomras on 2026-6-7
from __future__ import annotations
from typing import Optional, Callable, Any

from .field import FieldScope, ExtraMode, TraitField, Undefined
from mopplot.exceptions import TraitFieldException, TraitException, TypeException


class TraitConfig:
    __slots__ = ("extra_mode",)

    def __init__(self, extra_mode: ExtraMode = ExtraMode.Forbid):
        if not isinstance(extra_mode, ExtraMode):
            raise TypeException(
                f"extra_mode must be ExtraMode, got {type(extra_mode).__name__}"
            )
        self.extra_mode = extra_mode


def trait_validator(validator: Callable[[Any], None]) -> Callable[[Any], None]:
    # 检查validator之后再说
    if not callable(validator):
        raise TypeException(
            f"validator must be callable, got {type(validator).__name__}"
        )
    setattr(validator, "__is_trait_validator__", None)
    return validator


class _TraitMetaclass(type):
    def __new__(mcs, name, bases, namespace):
        if bases == (object,):
            return super().__new__(mcs, name, bases, namespace)

        mcs._trait_config(namespace)
        cls = super().__new__(mcs, name, bases, namespace)

        # 找父Trait
        __parent_trait__ = mcs._parse_trait_inherit(bases)
        setattr(cls, "__parent_trait__", __parent_trait__)
        # 预留
        setattr(cls, "__subtraits__", {})
        setattr(cls, "__fields__", {})

        # 继承父Trait字段
        if __parent_trait__:
            mcs._inherit_parent_fields(__parent_trait__, cls)

        # 收集本类字段
        mcs._write_local_fields(name, namespace, cls)
        mcs._validator(namespace, cls)
        return cls

    @classmethod
    def _parse_trait_inherit(mcs, bases):
        trait_bases = set()

        for base in bases:
            for cls in getattr(base, "__mro__", ()):
                if cls is object:
                    continue
                if is_trait(cls):
                    trait_bases.add(cls)

        if len(trait_bases) > 1:
            names = ", ".join(cls.__name__ for cls in trait_bases)
            raise TraitException(f"Cannot inherit multiple Trait subclasses: {names}")

        return trait_bases.pop() if trait_bases else None

    @classmethod
    def _trait_config(mcs, namespace) -> None:
        annotations = namespace.get("__annotations__", {})
        if "trait_config" in annotations:
            del annotations["trait_config"]
        if "trait_config" not in namespace:
            namespace["trait_config"] = TraitConfig()
        elif not isinstance(namespace["trait_config"], TraitConfig):
            raise TraitException("Keyword 'trait_config' must be TraitConfig")
        namespace["__trait_extra__"] = {}

    @classmethod
    def _inherit_parent_fields(mcs, parent_trait, cls):
        """
        将父Trait字段继承到子Trait，遵循 private/protected 规则。
        private → 不继承
        """
        parent_fields = getattr(parent_trait, "__fields__")
        child_fields = getattr(cls, "__fields__")

        for fname, field in parent_fields.items():
            if field.scope != FieldScope.Private:
                child_fields[fname] = field.clone()

    @classmethod
    def _write_local_fields(mcs, name, namespace, cls):
        annotations = namespace.get("__annotations__", {})
        fields = getattr(cls, "__fields__")

        for fname, ftype in annotations.items():
            if not TraitField.available_type(ftype):
                raise TypeException(f"Unavailable type: {type(ftype).__name__}")

            value = namespace.get(fname, Undefined)
            parent_field = fields.get(fname)

            # 根据value生成TraitField
            if isinstance(value, TraitField):
                if (
                    (not value.omissible)
                    and (not value.has_value)
                    and (value.scope != FieldScope.Public)
                ):
                    raise TraitException(
                        f"TraitField '{fname}' is {value.scope.name.lower()} but has no default value. "
                        f"Private and protected fields must provide a default or a default_factory."
                    )
                field = value
                if parent_field is not None:
                    if field._is_default_scope:
                        field.scope = parent_field.scope
                        field._is_default_scope = False
                    if field._is_default_omissible:
                        field.omissible = parent_field.omissible
                        field._is_default_omissible = False

            elif value is Undefined:
                if parent_field is not None:
                    field = TraitField(
                        scope=parent_field.scope, omissible=parent_field.omissible
                    )
                else:
                    field = TraitField()
            else:
                if not TraitField.check_value_type(value, ftype):
                    raise TypeException(f"default {value!r} failed type validator")
                if parent_field is not None:
                    field = TraitField(
                        default=value,
                        scope=parent_field.scope,
                        omissible=parent_field.omissible,
                    )
                else:
                    field = TraitField(default=value)

            field.__field_annotation__ = ftype
            fields[fname] = field

    @classmethod
    def _validator(mcs, namespace, cls):
        setattr(cls, "__trait_validators__", [])
        for v in namespace.values():
            if hasattr(v, "__is_trait_validator__"):
                cls.__trait_validators__.append(v)  # type: ignore


class Trait(metaclass=_TraitMetaclass):
    def __init__(self, **kwargs):
        fields = self.__class__.__fields__  # type: ignore

        unknown = kwargs.keys() - fields.keys()
        if unknown:
            match self.trait_config.extra_mode:  # type: ignore
                case ExtraMode.Forbid:
                    raise TraitException(f"Unknown fields: {', '.join(unknown)}")
                case ExtraMode.Allow:
                    for k in unknown:
                        v = kwargs[k]
                        self.__trait_extra__[k] = v  # type: ignore
                        super().__setattr__(k, v)
                case ExtraMode.Ignore:
                    pass

        for fname, field in fields.items():
            if fname in kwargs:
                value = field.generate_value(kwargs[fname])
                if field.scope == FieldScope.Private:
                    raise TraitException(f"Cannot initialize a private field {fname}")
                if field.scope == FieldScope.Protected:
                    raise TraitException(f"Cannot initialize a protected field {fname}")
            else:
                value = field.default_value()
                if value is Undefined:
                    if not field.omissible:
                        raise TraitException(f"Missing required field: {fname}")
                    continue

            super().__setattr__(fname, value)

        for validator in self.__class__.__trait_validators__:  # type: ignore
            try:
                validator(self)
            except Exception as e:
                raise TraitException(
                    f"Failed trait validator '{validator.__name__}'"
                ) from e

        self.trait_init()

    def trait_init(self) -> None: ...

    @classmethod
    def provide_validator(
        cls, *, enable_generator: bool = True
    ) -> Callable[[dict[str, Any]], None]:
        if cls is Trait:
            raise NotImplemented
        if not isinstance(enable_generator, bool):
            raise TypeException(
                f"enable_generator must be bool, got {type(enable_generator).__name__}"
            )

        def validator(kwargs: dict[str, Any]) -> None:
            if not isinstance(kwargs, dict):
                raise TypeException(
                    f"kwargs must be dict[str, Any], got {type(kwargs).__name__}"
                )

            fields = cls.__fields__  # type: ignore
            fields = {
                fname: field
                for fname, field in fields.items()
                if field.scope == FieldScope.Public
            }

            unknown = kwargs.keys() - fields.keys()
            if cls.trait_config.extra_mode == ExtraMode.Forbid and unknown:  # type: ignore
                raise TraitException(f"Unknown fields: {', '.join(unknown)}")

            for fname, field in fields.items():
                if fname in kwargs:
                    value = kwargs[fname]
                    if field.generator is not None and enable_generator:
                        value = field.generator(value)
                    field.validate_value(value)
                elif not field.omissible:
                    raise TraitException(f"Missing required field: {fname}")

            return True

        return validator

    def __setattr__(self, name, value):
        fields = self.__class__.__fields__  # type: ignore

        if name in fields:
            field = fields[name]
            if field.scope == FieldScope.Private:
                raise TraitException(f"Cannot modify a private field {name}")
            if field.scope == FieldScope.Protected:
                raise TraitException(f"Cannot modify a protected field {name}")

            field.validate_value(value)
        else:
            match self.trait_config.extra_mode:  # type: ignore
                case ExtraMode.Forbid:
                    raise TraitException(f"Unknown field: {name}")
                case ExtraMode.Allow:
                    self.__trait_extra__[name] = value  # type: ignore
                case ExtraMode.Ignore:
                    pass

        super().__setattr__(name, value)

    @classmethod
    def _next_required_trait(cls) -> Optional[type[Trait]]:
        cur_trait = cls.__parent_trait__  # type: ignore
        while cur_trait is not None:
            if not cur_trait.__collapsible__:
                return cur_trait
            cur_trait = cur_trait.__parent_trait__
        return None

    def contains(self, field_name: str) -> bool:
        if not isinstance(field_name, str):
            raise TypeException(
                f"field_name must be str, got {type(field_name).__name__}"
            )
        if field_name not in self.__class__.__fields__:  # type: ignore
            return False
        return field_name in self.__dict__

    def get_data(self) -> dict[str, Any]:
        result = {}
        for fname, field in self.__class__.__fields__.items():  # type: ignore
            if fname in self.__dict__:
                result[fname] = getattr(self, fname)
        return result


def is_trait(cls):
    return isinstance(cls, type) and issubclass(cls, Trait) and cls is not Trait
