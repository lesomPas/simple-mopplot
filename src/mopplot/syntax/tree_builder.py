# created by lesomras on 2026-6-20

from __future__ import annotations

import hashlib
from typing import Optional
from dataclasses import dataclass

from mopplot.lexer import Param, ParamKind, PatternLexer, DefaultPatternLexer


START = "start"
LF = "LF"


class PatternTree:
    def __init__(self, name: str, has_lf: bool = False, next_nonterm: Optional[str] = None):
        self.name = name
        self.has_lf = has_lf
        self.next_nonterm = next_nonterm
        self.children: dict[str, PatternTree] = {}

        self._cache_fingerprint: Optional[str] = None

    """
    def add_children(self, node: PatternTree) -> None:
        assert node.name not in self.children, "name collision"
        self.children[node.name] = node
    """

    def add_pattern(self, pattern: str, next_nonterm: str, lexer: PatternLexer) -> None:
        cur_node = self
        for param in lexer.tokenize(pattern):
            name = param.lexeme

            if param.kind == ParamKind.Optional:
                cur_node.has_lf = True
            if name not in cur_node.children:
                new_node = PatternTree(name)
                cur_node.children[name] = new_node
                cur_node = new_node
                continue
            cur_node = cur_node.children[name]

        if next_nonterm == LF:
            cur_node.has_lf = True
        cur_node.next_nonterm = next_nonterm

    @classmethod
    def nonterm(cls, nonterm: str, syntax: list, lexer: PatternLexer) -> PatternTree:
        root = cls(nonterm)
        for pattern in syntax:
            if isinstance(pattern, str):
                next_nonterm = LF
            else:
                assert len(pattern) >= 2, "invalid pattern"
                next_nonterm = pattern[1]
                pattern = pattern[0]

            assert pattern != LF, "name collision"
            root.add_pattern(pattern, next_nonterm, lexer)
        return root

    def get_children(self) -> list[PatternTree]:
        return list(self.children.values())

    def _compute_fingerprint(self) -> str:
        """
        计算当前节点的哈希指纹，代表该节点的 suffix tree。
        只考虑当前节点及其子节点（不展开 next_nonterm），
        子节点按名称排序以保证无序性。
        """
        # 1. 自身信息
        parts = [
            self.name,
            str(self.has_lf),
            self.next_nonterm or "NONE",
        ]

        # 2. 收集所有子节点指纹（按子节点名称排序）
        child_fps = []
        for child_name in sorted(self.children.keys()):
            child = self.children[child_name]
            child_fps.append(f"{child_name}:{child.fingerprint}")
        # 将子节点指纹列表用分隔符连接，作为整体的一部分
        parts.append("|".join(child_fps))

        # 3. 组合成字符串并哈希
        combined = "||".join(parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    @property
    def fingerprint(self) -> str:
        if self._cache_fingerprint is not None:
            return self._cache_fingerprint
        return self._compute_fingerprint()


@dataclass(slots=True)
class SyntaxResult:
    rename_mapping: dict[str, dict[str, str]]
    ast: dict[str, list[str]]


class AstTreeBuilder:
    def __init__(self, data: dict[str, list], lexer: PatternLexer = DefaultPatternLexer()):
        self.data = data
        self.lexer = lexer

    def build(self) -> SyntaxResult:
        nonterms = self.original_tree(self.data, self.lexer)
        collisions = self.find_duplicate_nodes(nonterms)

        rename_mapping = {}
        for name, collision in collisions.items():
            fingerprints = self.get_fingerprints(collision)
            rename_mapping[name] = {fp: f"{name}'{i}" for i, fp in enumerate(fingerprints, start=1)}

        original_ast = self._build_ast(nonterms, rename_mapping)

        return SyntaxResult(
            rename_mapping=rename_mapping,
            ast=original_ast,
        )

    @staticmethod
    def _build_ast(nonterms: dict[str, PatternTree], rename_mapping: dict[str, dict[str, str]]) -> dict[str, list[str]]:
        def get_name(node: PatternTree) -> str:
            if node.name not in rename_mapping:
                return node.name
            return rename_mapping[node.name][node.fingerprint]

        nonterm_entry = {}
        nonterm_entry_has_lf = {}
        for nonterm, tree in nonterms.items():
            seq = tree.get_children()
            nonterm_entry[nonterm] = [get_name(child) for child in seq]
            for child in seq:
                if child.has_lf:
                    nonterm_entry_has_lf[nonterm] = True
                    break
            else:
                nonterm_entry_has_lf[nonterm] = False

        need_compiling_nonterm = [START]
        compiled_nonterm = []

        edges: dict[str, list[str]] = {}

        def add_edge(parent: str, child: str):
            if parent not in edges:
                edges[parent] = [child]
            elif child not in edges[parent]:
                edges[parent].append(child)

        def traverse(node: PatternTree):
            node_name = get_name(node)

            for child in node.children.values():
                child_name = get_name(child)
                add_edge(node_name, child_name)

            if node.next_nonterm and node.next_nonterm != LF:
                target = node.next_nonterm
                if target not in compiled_nonterm and target not in need_compiling_nonterm:
                    need_compiling_nonterm.append(target)
                for entry in nonterm_entry[target]:
                    add_edge(node_name, entry)
                if nonterm_entry_has_lf[target]:
                    add_edge(node_name, LF)

            if node.has_lf:
                add_edge(node_name, LF)

            for child in node.children.values():
                traverse(child)

        def compile_nonterm(nonterm: PatternTree):
            for head_node in nonterm.get_children():
                traverse(head_node)
            compiled_nonterm.append(nonterm)

        # 循环检测我不做了
        while len(need_compiling_nonterm) != 0:
            nonterm_name = need_compiling_nonterm.pop(0)
            if nonterm_name not in nonterms:
                raise ValueError # 再等等
            compile_nonterm(nonterms[nonterm_name])

        return edges

    @staticmethod
    def original_tree(nonterms: dict[str, list], lexer: PatternLexer) -> dict[str, PatternTree]:
        result = {}
        for nonterm, syntax in nonterms.items():
            result[nonterm] = PatternTree.nonterm(nonterm, syntax, lexer)
        return result

    @staticmethod
    def find_duplicate_nodes(trees: dict[str, PatternTree]) -> dict[str, list[PatternTree]]:
        name_to_nodes: dict[str, list[PatternTree]] = {}

        def collect(node: PatternTree) -> None:
            """递归收集节点及其所有子节点"""
            name_to_nodes.setdefault(node.name, []).append(node)
            for child in node.children.values():
                collect(child)

        for tree in trees.values():
            collect(tree)

        return {name: nodes for name, nodes in name_to_nodes.items() if len(nodes) > 1}

    @staticmethod
    def get_fingerprints(duplicate_nodes: list[PatternTree]) -> set[str]:
        return {node.fingerprint for node in duplicate_nodes}
