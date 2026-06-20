# created by lesomras on 2026-6-11

from mopplot.trait import FieldScope, field, Trait, TraitLib

chelper = TraitLib(lib_name="chr")

@chelper("node", collapsible=True)
class Node(Trait):
    type: str = field(default="", scope=FieldScope.Protected)
    id: str
    brief: str = field(omissible=True)
    description: str = field(omissible=True)


class SequenceItem(Trait):
    name: str
    description: str = field(omissible=True)
