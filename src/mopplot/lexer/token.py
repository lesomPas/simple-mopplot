# created by lesomras at 2026-5-30
"""The basic component for command lexer"""

from dataclasses import dataclass
from enum import StrEnum


class ParamKind(StrEnum):
    """Type of a lexical parameter"""

    Identifier = "identifier"
    Required = "required"
    Optional = "optional"


@dataclass(slots=True)
class Param:
    """
    Represents a single lexical parameter from a command pattern.

    :kind: The type of the parameter.
    :lexeme: The raw string matched from the source pattern.
    :start: Starting index (inclusive) in the original pattern string.
    :end: Ending index (exclusive) in the original pattern string.
    """

    kind: ParamKind
    lexeme: str
    start: int
    end: int
