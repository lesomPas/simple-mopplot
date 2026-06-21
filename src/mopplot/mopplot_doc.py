# created by lesomras on 2026-6-18

# from __future__ import annotations

from typing import Any, Optional

from mopplot.exceptions import MopplotDocException
from mopplot.trait import field, Trait, trait_validator, TraitConfig, ExtraMode
from mopplot.chelper import chelper
from mopplot.syntax.tree_builder import AstTreeBuilder


class MopplotDocTrait(Trait):
    trait_config = TraitConfig(
        extra_mode=ExtraMode.Ignore,
    )

    name: list[str]
    description: str = field(omissible=True)
    syntax: dict[str, list]
    node: dict[str, type[Trait]] = field(
        generator=lambda d: {k: chelper.get_trait(v) for k, v in d.items()},
    )
    init: dict[str, dict[str, Any]]

    @trait_validator
    def check_name(self) -> None:
        for name in self.name:
            if not name.isidentifier():
                raise MopplotDocException(
                    f"Elements of name must be identifier, got {name!r}"
                )

    @trait_validator
    def check_init(self) -> None:
        for i in self.init.values():
            if "id" in i:
                raise MopplotDocException(f"Keyboard 'id' can't be overrided, at {i!r}")


class MopplotDoc:
    def __init__(
        self,
        name: list[str],
        description: str,
        ast: dict[str, list[str]],
        command_head: str,
        trait_pool: list[Trait],
    ):
        self.name = name
        self.description = description
        self.ast = ast
        self.command_head = command_head
        self.trait_pool = trait_pool

    @classmethod
    def from_dict(cls, data: dict) -> "MopplotDoc":
        trait = MopplotDocTrait(**data)
        description = trait.description if trait.contains("description") else ""

        try:
            syntax_result = AstTreeBuilder(trait.syntax).build()
        except Exception as e:
            raise MopplotDocException("Build ast failed!") from e

        old_name_mapping = cls.old_name_mapping(syntax_result.rename_mapping)
        used_trait = cls.used_trait(syntax_result.ast)

        command_head: Optional[str] = None
        trait_pool = []

        for trait_name in used_trait:
            old_trait_name = old_name_mapping.get(trait_name, trait_name)
            if old_trait_name.startswith("/"):
                if command_head:
                    raise MopplotDocException(
                        f"Duplicate command head: '{old_trait_name}'"
                    )
                command_head = old_trait_name
                continue
            if old_trait_name not in trait.node:
                raise MopplotDocException(f"Not found trait '{old_trait_name}'")

            try:
                node_trait = trait.node[old_trait_name](
                    id=trait_name, **trait.init.get(old_trait_name, {})
                )
            except Exception as e:
                raise MopplotDocException("Build trait failed!") from e
            trait_pool.append(node_trait)

        if not command_head:
            raise MopplotDocException("Excepted a command head")

        return cls(trait.name, description, syntax_result.ast, command_head, trait_pool)

    @staticmethod
    def old_name_mapping(rename_mapping: dict[str, dict[str, str]]) -> dict[str, str]:
        result = {}
        for old_name, mapping in rename_mapping.items():
            for new_name in mapping.values():
                result[new_name] = old_name
        return result

    @staticmethod
    def used_trait(original_ast: dict[str, list[str]]) -> list[str]:
        return list(original_ast.keys())

    def to_dict(self) -> dict:
        final_dictionary = {}
        final_dictionary["name"] = self.name
        final_dictionary["description"] = self.description
        final_dictionary["start"] = self.ast.pop(self.command_head)
        final_dictionary["node"] = [t.get_data() for t in self.trait_pool]
        final_dictionary["ast"] = [[k] + v for k, v in self.ast.items()]
        return final_dictionary
