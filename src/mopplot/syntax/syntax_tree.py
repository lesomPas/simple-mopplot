# created by lesomras on 2026-6-21

from __future__ import annotations

import hashlib
from typing import Optional
from dataclasses import dataclass

from mopplot.lexer import Param, ParamKind, default_lexer

START = "start"

class SyntaxTree:
    """一种更简单的树结构"""
    def __init__(self, pattern: str, next_nonterm: Optional[str]):
        self.pattern = pattern
        self.next_nonterm = next_nonterm

        self.children: list[SyntaxTree] = []

    @staticmethod
    def resolve_tree_children(nonterms: dict[str, list]) -> dict[str, list[SyntaxTree]]:
        tree_children = {}
        for nonterm, syntax in nonterms.items():
            seq = []
            for pattern in syntax:
                if isinstance(pattern, list):
                    text = pattern[0]
                    next_nonterm = pattern[1]
                elif isinstance(pattern, str):
                    text = pattern
                    next_nonterm = None
                else:
                    raise ValueError # 再等等
                seq.append(SyntaxTree(text, next_nonterm))
            tree_children[nonterm] = seq
        return tree_children

    @staticmethod
    def resolve_nodes(tree_children: dict[str, list[SyntaxTree]]) -> list[str]:
        """提取所有词素，并按首次出现顺序去重。"""
        seen = {}
        for seq in tree_children.values():
            for tree in seq:
                for token in default_lexer.tokenize(tree.pattern):
                    seen.setdefault(token.lexeme, None)  # 保留插入顺序
        return list(seen.keys())

    @classmethod
    def original_tree(cls, tree_children: dict[str, list[SyntaxTree]]) -> SyntaxTree:
        def dfs(cur_node: SyntaxTree) -> None:
            if (nn := cur_node.next_nonterm) is not None:
                cur_node.children = tree_children[nn]
                cur_node.next_nonterm = None

                for child in cur_node.children:
                    dfs(child)

        result = SyntaxTree("start'internal", START)
        dfs(result)
        return result

    def get_all_paths(self) -> list[str]:
        """
        返回从根节点的子节点出发到所有叶子节点的路径。
        每条路径是一个字符串列表，表示从第一个有效词素到结束标记的序列。
        """
        paths = []
        current = []

        def dfs(node: SyntaxTree) -> None:
            if not node.children:
                # 叶子节点：记录当前路径（当前路径包含了从根开始的所有词素）
                paths.append(current.copy())
                return
            for child in node.children:
                current.append(child.pattern)
                dfs(child)
                current.pop()

        dfs(self)
        return [" ".join(p) for p in paths]
