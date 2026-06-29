# created by lesomras on 2026-6-21


def print_tree(node, prefix="", is_root=True, is_last=True):
    """打印树结构，显示每个节点的名字和指向的非终结符"""
    print_name = node.pattern

    if is_root:
        # 根节点特殊处理，不加连接线
        print(f"{print_name} (next={node.next_nonterm})")
        new_prefix = ""
    else:
        # 非根节点用 ASCII 画树
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{print_name} (next={node.next_nonterm})")
        new_prefix = prefix + ("    " if is_last else "│   ")

    # 递归打印所有子节点（字典按插入顺序，可观察冲突）
    children_list = list(node.children)
    for i, child in enumerate(children_list):
        print_tree(
            child,
            prefix=new_prefix,
            is_root=False,
            is_last=(i == len(children_list) - 1)
        )
