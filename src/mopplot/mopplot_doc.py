# created by lesomras on 2026-6-18

# from __future__ import annotations

from typing import Any, Optional

from mopplot.exceptions import MopplotDocException
from mopplot.trait import field, Trait, trait_validator, TraitConfig, ExtraMode
from mopplot.chelper import chelper
from mopplot.syntax.syntax_tree import SyntaxTree

class MopplotDocTrait(Trait):
    trait_config = TraitConfig(
        extra_mode=ExtraMode.Allow,
    )

    name: list[str]
    description: str = field(omissible=True)
    syntax: dict[str, list]
    node: dict[str, type[Trait]] = field(
        generator=lambda d: {k: chelper.get_trait(v) for k, v in d.items()},
    )
    # default_init: dict[str, dict[str, Any]]

    @trait_validator
    def check_name(self) -> None:
        for name in self.name:
            if not name.isidentifier():
                raise MopplotDocException(
                    f"Elements of name must be identifier, got {name!r}"
                )

class MopplotDoc:
    def __init__(
        self,
        name: list[str],
        description: str,
        syntax: list[str],
        trait_pool: dict[str, Trait],
    ):
        self.name = name
        self.description = description
        self.syntax = syntax
        self.trait_pool = trait_pool

    @classmethod
    def from_dict(cls, data: dict) -> "MopplotDoc":
        doc_trait = MopplotDocTrait(**data)
        doc_name, doc_description = cls._get_name_description(doc_trait)

        try:
            doc_syntax, nodes = cls._get_paths_nodes(doc_trait)
        except Exception as e:
            raise MopplotDocException("Build ast failed!") from e

        cls._precheck(doc_trait, nodes)
        builders, datas = cls._build_trait_info(doc_trait)
        doc_trait_pool = cls._build_trait_pool(doc_trait, nodes, builders, datas)

        return cls(doc_name, doc_description, doc_syntax, doc_trait_pool)

    @staticmethod
    def _get_name_description(trait: MopplotDocTrait) -> tuple[list[str], str]:
        description = trait.description if trait.contains("description") else ""
        return trait.name, description

    @staticmethod
    def _get_paths_nodes(trait: MopplotDocTrait) -> tuple[list[str], list[str]]:
        tree_children = SyntaxTree.resolve_tree_children(trait.syntax)
        paths = SyntaxTree.original_tree(tree_children).get_all_paths()
        nodes = SyntaxTree.resolve_nodes(tree_children)
        return paths, nodes

    @staticmethod
    def _precheck(trait: MopplotDocTrait, nodes: list[str]) -> None:
        has_command_head = False

        # 预检查
        for node_name in nodes:
            if node_name.startswith("/"):
                if has_command_head:
                    raise MopplotDocException(f"Duplicate command head: '{node_name}'")
                has_command_head = True
                continue

            if node_name not in trait.node:
                raise MopplotDocException(f"Not found trait '{node_name}'")

        if not has_command_head:
            raise MopplotDocException("Excepted a command head")

    @staticmethod
    def _build_trait_info(trait: MopplotDocTrait) -> tuple:
        trait_builder: dict[str, str] = {}
        trait_data: dict[str, dict[str, Any]] = {}

        for builder_name, builder_data in trait.__trait_extra__.items(): # type: ignore
            if not isinstance(builder_data, dict):
                raise MopplotDocException(
                    f"The value in '{builder_name}' must be dict[str, Any], got {type(builder_data).__name__} in builder '{builder_name}'"
                )
            for node_name, node_data in builder_data.items():
                assert isinstance(node_name, str), f"The key in builder data '{builder_name}' must be str, got {type(node_name).__name__}"
                assert all(isinstance(k, str) for k in node_data), f"The key in node data '{node_name}' must be str"

                if node_name in trait_builder:
                    raise MopplotDocException(f"Node '{node_name}' has duplicate trait builder '{trait_builder[node_name]}', got '{builder_name}'")
                trait_builder[node_name] = builder_name
                trait_data[node_name] = node_data

        return trait_builder, trait_data

    @staticmethod
    def _build_trait_pool(doc_trait: MopplotDocTrait, nodes: list[str], builders, datas) -> dict[str, Trait]:
        trait_pool: dict[str, Trait] = {}
        for node_name in nodes:
            if node_name.startswith("/"):
                continue

            trait = doc_trait.node[node_name]
            if node_name in builders:
                try:
                    builder_function = trait.get_builder(builders[node_name], key=node_name)
                except Exception as e:
                    raise MopplotDocException(f"Not found builder '{builders[node_name]}' in trait '{getattr(trait, '__trait_name__', trait.__name__)}'") from e

                try:
                    trait_obj = builder_function(**datas[node_name])
                except Exception as e:
                    raise MopplotDocException(f"Trait builder '{builders[node_name]}' in trait '{getattr(trait, '__trait_name__', trait.__name__)}' failed") from e
            else:
                try:
                    trait_obj = trait()
                except Exception as e:
                    raise MopplotDocException(f"default_init in trait '{getattr(trait, '__trait_name__', trait.__name__)}' failed, maybe you need to provide args") from e

            trait_pool[node_name] = trait_obj

        return trait_pool

    def to_dict(self) -> dict:
        final_dictionary = {}
        final_dictionary["name"] = self.name
        final_dictionary["description"] = self.description
        final_dictionary["syntax"] = self.syntax
        final_dictionary["node"] = {k: v.get_data() for k, v in self.trait_pool.items()}
        return final_dictionary
