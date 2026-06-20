# created by lesomras on 2026-6-7

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from typing import get_origin, get_args

from mopplot.exceptions import TypeException, InvalidValueException, TraitFieldException

Undefined = object()


class FieldScope(Enum):
    Private = "FieldScope.Private"
    Protected = "FieldScope.Protected"
    Public = "FieldScope.Public"


class ExtraMode(Enum):
    Ignore = "ExtraMode.Ignore"
    Forbid = "ExtraMode.Forbid"
    Allow = "ExtraMode.Allow"


T = TypeVar("T")


class TraitField:
    __slots__ = (
        "default",
        "default_factory",
        "validator",
        "generator",
        "scope",
        "omissible",
        "__field_annotation__",
        "_is_default_scope",
        "_is_default_omissible",
    )

    def __init__(
        self,
        *,
        default: T = Undefined,
        default_factory: Optional[Callable[[], T]] = None,
        validator: Optional[Callable[[Any], bool]] = None,
        generator: Optional[Callable[[Any], T]] = None,
        scope: Optional[FieldScope] = None,
        omissible: Optional[bool] = None,
    ):
        # ---------- parameter validation ----------
        if scope is not None and not isinstance(scope, FieldScope):
            raise TypeException("")

        if omissible is not None and not isinstance(omissible, bool):
            raise TypeException("")

        if validator is not None and not callable(validator):
            raise TypeException("validator must be callable")

        if default_factory is not None and not callable(default_factory):
            raise TypeException("default_factory must be callable")

        if generator is not None and not callable(generator):
            raise TypeException("generator must be callable")

        # ---------- semantic validation ----------
        if default is not Undefined and default_factory is not None:
            raise InvalidValueException(
                "Cannot specify both default and default_factory"
            )

        # ---------- assign ----------
        self.__field_annotation__ = Undefined

        self.default = default
        self.default_factory = default_factory
        self.validator = validator
        self.generator = generator

        self.scope = scope if scope is not None else FieldScope.Public
        self._is_default_scope = scope is None

        self.omissible = omissible if omissible is not None else False
        self._is_default_omissible = omissible is None

        # ---------- validate default ----------
        if default is not Undefined:
            if self.validator and not self.validator(default):
                raise TraitFieldException(f"default {default!r} failed validator")

    @staticmethod
    def available_type(t) -> bool:
        if t is None:
            return True
        if t is type(None):
            return True
        if t is Any:
            return True

        origin = get_origin(t)

        if origin is list:
            args = get_args(t)
            if len(args) != 1:
                return False
            return TraitField.available_type(args[0])

        if origin is dict:
            args = get_args(t)
            if len(args) != 2:
                return False
            key_t, value_t = args
            return TraitField.available_type(key_t) and TraitField.available_type(value_t)

        if origin is type:
            args = get_args(t)
            if len(args) != 1:
                return False
            return TraitField.available_type(args[0])

        return isinstance(t, type)

    @staticmethod
    def check_value_type(value, t) -> bool:
        if t is Undefined:
            return True

        if t is Any:
            return True

        if t is None:
            return value is None

        if t is type(None):
            return value is None

        origin = get_origin(t)

        # 普通类型
        if origin is None:
            return isinstance(value, t)

        # list[T]
        if origin is list:
            if not isinstance(value, list):
                return False

            item_t = get_args(t)[0]

            return all(TraitField.check_value_type(v, item_t) for v in value)

        # dict[K, V]
        if origin is dict:
            if not isinstance(value, dict):
                return False

            key_t, value_t = get_args(t)
            for k, v in value.items():
                if not TraitField.check_value_type(k, key_t):
                    return False
                if not TraitField.check_value_type(v, value_t):
                    return False
            return True

        # type[T]
        if origin is type:
            args = get_args(t)
            if args:
                # 检查 value 是否为类，并且是否为 args[0] 的子类
                return isinstance(value, type) and issubclass(value, args[0])
            return isinstance(value, type)

        return False

    def validate_value(self, value):
        if not self.check_value_type(value, self.__field_annotation__):
            raise TypeException(f"Value {value!r} failed type validator")
        if self.validator and not self.validator(value):
            raise TraitFieldException(f"Value {value!r} failed validator")

    def default_value(self) -> Any:
        if self.default is not Undefined:
            return self.default
        if self.default_factory is not None:
            value = self.default_factory()
            self.validate_value(value)
            return value
        return Undefined

    def generate_value(self, value: Any) -> Any:
        # if value is Undefined:
        #     return self.default_value()
        if self.generator is not None:
            value = self.generator(value)
        self.validate_value(value)
        return value

    @property
    def has_value(self) -> bool:
        return self.default is not Undefined or self.default_factory is not None

    @property
    def can_skip(self) -> bool:
        return self.has_value or self.omissible

    def clone(self) -> TraitField:
        f = TraitField(
            default=self.default,
            default_factory=self.default_factory,
            validator=self.validator,
            generator=self.generator,
            scope=self.scope,
            omissible=self.omissible,
        )
        f.__field_annotation__ = self.__field_annotation__
        return f

    def __repr__(self) -> str:
        parts = []

        # 处理 default / default_factory
        if self.default is not Undefined:
            parts.append(f"default={self.default!r}")
        elif self.default_factory is not None:
            parts.append(
                f"default_factory={getattr(self.default_factory, '__name__', repr(self.default_factory))}"
            )

        if self.validator is not None:
            parts.append(f"validator={self.validator.__name__}")
        if self.scope != FieldScope.Public:
            parts.append(f"scope={self.scope.value}")

        return f"TraitField({', '.join(parts)})"


def field(
    *,
    default: Any = Undefined,
    default_factory: Optional[Callable[[], Any]] = None,
    validator: Optional[Callable[[Any], bool]] = None,
    generator: Optional[Callable[[Any], T]] = None,
    scope: FieldScope = FieldScope.Public,
    omissible: bool = False,
) -> Any:
    return TraitField(
        default=default,
        default_factory=default_factory,
        validator=validator,
        generator=generator,
        scope=scope,
        omissible=omissible,
    )
