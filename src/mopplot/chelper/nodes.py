# created by lesomras on 2026-6-11

from mopplot.trait import field, trait_validator
from .bases import chelper, Node, SequenceItem
from .seq_validator import seq_validator


@chelper("block")
class Block(Node):
    type: str = "BLOCK"
    nodeBlockType: int = field(validator=lambda n: n in (0, 1))


@chelper("boolean")
class Boolean(Node):
    type: str = "BOOLEAN"
    descriptionTrue: str = ""
    descriptionFalse: str = ""


@chelper("command")
class Command(Node):
    type: str = "COMMAND"


@chelper("command_name")
class CommandName(Node):
    type: str = "COMMAND_NAME"


@chelper("float")
class Float(Node):
    type: str = "FLOAT"
    min: float = field(omissible=True)
    max: float = field(omissible=True)


@chelper("integer")
class Integer(Node):
    type: str = "INTEGER"
    min: int = field(omissible=True)
    max: int = field(omissible=True)


@chelper("integer_with_unit")
class IntegerWithUnit(Node):
    type: str = "INTEGER_WITH_UNIT"
    units: list = field(
        validator=seq_validator(SequenceItem.provide_validator())
    )


@chelper("item")
class Item(Node):
    type: str = "ITEM"
    nodeItemType: int = field(validator=lambda n: n in (0, 1))


class ContentsItem(SequenceItem):
    idNamespace: str = "minecraft"


@chelper("namespace_id")
class NamespaceId(Node):
    type: str = "NAMESPACE_ID"
    key: str = field(omissible=True)
    ignoreError: bool = False
    contents: list = field(
        validator=seq_validator(ContentsItem.provide_validator()),
        omissible=True
    )

    @trait_validator
    def check_key_contents(self) -> None:
        if not self.contains("key") and not self.contains("contents"):
            raise ValueError("key and constants are at least one occurrence of")


@chelper("normal_id")
class NormalId(Node):
    type: str = "NORMAL_ID"
    key: str = field(omissible=True)
    ignoreError: bool = False
    contents: list = field(
        validator=seq_validator(SequenceItem.provide_validator()),
        omissible=True
    )

    @trait_validator
    def check_key_contents(self) -> None:
        if not self.contains("key") and not self.contains("contents"):
            raise ValueError("key and constants are at least one occurrence of")


@chelper("position")
class Position(Node):
    type: str = "POSITION"


@chelper("relative_float")
class RelativeFloat(Node):
    type: str = "RELATIVE_FLOAT"
    canUseCaretNotation: bool = True


# Repeat 我再考虑考虑

@chelper("string")
class String(Node):
    type: str = "STRING"
    canContainSpace: bool
    ignoreLater: bool


@chelper("target_selector")
class TargetSelector(Node):
    type: str = "TARGET_SELECTOR"
    isOnlyOne: bool = False
    isMustPlayer: bool = False
    isMustNPC: bool = False
    isWildcard: bool = False


@chelper("text")
class Text(Node):
    type: str = "TEXT"
    data: dict = field(
        validator=SequenceItem.provide_validator()
    )


@chelper("range")
class Range(Node):
    type: str = "RANGE"


