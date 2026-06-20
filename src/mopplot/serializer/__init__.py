# create by lesomras on 2025-12-17
from .json_serializer import (
    JsonSerializer,      # 普通JSON序列化器
    CompactSerializer,   # 紧凑JSON序列化器
    load_json,           # 快捷函数：加载JSON
    loads_json,          # 快捷函数：从字符串加载JSON
    dump_json,           # 快捷函数：保存JSON
    dumps_json,          # 快捷函数：序列化为JSON字符串
    dump_json_compact,   # 快捷函数：保存紧凑JSON
    dumps_json_compact,  # 快捷函数：序列化为紧凑JSON字符串
    dumps_command,       # 快捷函数: 针对面临特殊处理的序列化函数(str)
)

__all__= [
    "JsonSerializer",
    "CompactSerializer",
    "load_json",
    "loads_json",
    "dump_json",
    "dumps_json",
    "dumps_command",
    "dump_json_compact",
    "dumps_json_compact",
]