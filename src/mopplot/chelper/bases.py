# created by lesomras on 2026-6-11

from typing import Any

from mopplot.trait import FieldScope, field, Trait, TraitLib
from mopplot.exceptions import TraitException

chelper = TraitLib(lib_name="chr")


@chelper("node", collapsible=True)
class Node(Trait):
    type: str = field(default="", scope=FieldScope.Protected)
    brief: str = field(omissible=True)
    description: str = field(omissible=True)


class SequenceItem(Trait):
    name: str
    description: str = field(omissible=True)
