# created by lesomras on 2025-5-31

import re
from .trait import Trait
from mopplot.exceptions import (
    TypeException,
    InvalidValueException,
    TraitPathException,
    TraitLibException,
)

PATH_PATTERN = re.compile(r"^[^:]+(?:::[^:]+)*$")


class TraitLib:
    _libraries: dict[str, "TraitLib"] = {}
    _is_init: bool = False

    def __init__(self, lib_name: str):
        if not isinstance(lib_name, str):
            raise TypeException(f"lib_name must be str, got {type(lib_name).__name__}")

        if "::" in lib_name:
            raise InvalidValueException(
                f"Unexpected trait path in library name at pos {lib_name.find('::') + 1}."
            )

        lib_name = lib_name.strip()
        if not lib_name:
            raise InvalidValueException("Library name cannot be empty")

        if lib_name in self._libraries:
            raise TraitLibException(f"The library named {lib_name!r} already exists.")

        self.lib_name = lib_name
        self._libraries[lib_name] = self

        # 保存所有 trait 类及其名称
        self._trait_info = []
        self._ptr = 0

        # 根节点
        self.__root__: dict[str, type[Trait]] = {}

    def __call__(self, trait_name: str, *, collapsible: bool = False):
        """装饰器方式注册 Trait"""
        self._is_init = False
        if not isinstance(trait_name, str):
            raise TypeException(
                f"trait_name must be str, got {type(trait_name).__name__}"
            )
        if not isinstance(collapsible, bool):
            raise TypeException(
                f"collapsible must be bool, got {type(collapsible).__name__}"
            )

        trait_name = trait_name.strip()
        if not trait_name:
            raise InvalidValueException("Trait name cannot be empty")
        if "::" in trait_name:
            raise InvalidValueException(
                f"Trait name cannot contain '::' at pos {trait_name.find('::') + 1}."
            )

        def decorator(cls: type[Trait]):
            setattr(cls, "__trait_lib__", self.lib_name)
            setattr(cls, "__trait_name__", trait_name)
            setattr(cls, "__collapsible__", collapsible)
            self._trait_info.append((cls, trait_name))
            return cls

        return decorator

    def _continue_build_tree(self) -> None:
        """按注册顺序构建 trait 树"""
        while self._ptr < len(self._trait_info):
            trait_cls, name = self._trait_info[self._ptr]
            parent_trait = trait_cls.__parent_trait__

            # 根节点处理
            if parent_trait is None:
                if name in self.__root__:
                    raise TraitLibException(
                        f"Cannot register root trait '{name}' in library '{self.lib_name}': "
                        "a root trait with this name already exists. "
                        "Consider renaming the trait."
                    )
                self.__root__[name] = trait_cls
                self._ptr += 1
                continue

            # 如果父 trait 与当前 trait 不在同一个库
            if parent_trait.__trait_lib__ != trait_cls.__trait_lib__:  # type: ignore
                if name in self.__root__:
                    raise TraitLibException(
                        f"Cannot register root trait '{name}' in library '{self.lib_name}': "
                        "a root trait with this name already exists. "
                        "Consider renaming the trait."
                    )
                self.__root__[name] = trait_cls

            # 子 trait 处理
            parent_subtraits = parent_trait.__subtraits__
            if name in parent_subtraits:
                raise TraitLibException(
                    f"Cannot register trait '{name}' under parent trait '{parent_trait.__trait_name__}': "
                    "a subtrait with this name already exists. "
                    "Rename the trait or check your trait hierarchy to avoid conflicts."
                )
            parent_subtraits[name] = trait_cls

            # 如果父 trait 是 collapsible，需要检查“下一必需父 trait”
            if not parent_trait.__collapsible__:
                self._ptr += 1
                continue

            required_trait = parent_trait._next_required_trait()
            if required_trait is None:
                # 注册到根节点
                if name in self.__root__:
                    raise TraitLibException(
                        f"Cannot register trait '{name}' at root: a root trait with this name already exists. "
                        f"Conflict caused by collapsible parent trait '{parent_trait.__trait_name__}'."
                    )
                self.__root__[name] = trait_cls
            else:
                # 注册到下一必需父 trait
                if name in required_trait.__subtraits__:
                    raise TraitLibException(
                        f"Cannot register trait '{name}' under parent trait '{required_trait.__trait_name__}': "
                        f"conflict due to collapsible ancestor '{parent_trait.__trait_name__}'. "
                        "Rename the trait or adjust the collapsible setting."
                    )
                required_trait.__subtraits__[name] = trait_cls

            self._ptr += 1

    def init(self) -> None:
        """初始化库，构建树"""
        self._continue_build_tree()

    @classmethod
    def initialize(cls) -> None:
        """一次性初始化所有库"""
        if cls._is_init:
            return
        for lib in cls._libraries.values():
            lib._continue_build_tree()
        cls._is_init = True

    @staticmethod
    def _parse_trait_path(path: str) -> list[str]:
        if not PATH_PATTERN.fullmatch(path):
            raise TraitPathException(f"Invalid trait path: '{path}'")
        return path.split("::")

    @classmethod
    def get_trait(cls, path: str, default_lib: str = "std") -> type[Trait]:
        """通过路径查找 trait"""
        cls.initialize()

        if not isinstance(path, str):
            raise TypeException("Trait path must be a string")

        parts = cls._parse_trait_path(path)
        if not parts:
            raise TraitPathException("Trait path is empty")

        # 确定库
        first_part = parts[0]
        if first_part in cls._libraries:
            lib = cls._libraries[first_part]
            if len(parts) < 2:
                raise TraitLibException(
                    f"Path '{path}' must include at least one trait name after library"
                )
            idx = 1
        else:
            if default_lib not in cls._libraries:
                raise TraitLibException(
                    f"Default library '{default_lib}' does not exist"
                )
            lib = cls._libraries[default_lib]
            idx = 0

        # 遍历路径找到 trait
        try:
            cur_trait = lib.__root__[parts[idx]]
            idx += 1
            while idx < len(parts):
                cur_trait = cur_trait.__subtraits__[parts[idx]]  # type: ignore
                idx += 1
            return cur_trait
        except KeyError as e:
            raise TraitLibException(
                f"Trait '{parts[idx]}' not found at trait path '{path}'"
            ) from e


# 创建标准库
std = TraitLib(lib_name="std")
