# created by lesomras on 2026-5-30
"""Pattern string lexer for command patterns."""

from typing import Protocol, Iterator

from mopplot.exceptions import PatternLexerException
from .param import ParamKind, Param


class PatternLexer(Protocol):
    """Protocol for tokenizing a command pattern string."""

    def tokenize(self, pattern: str) -> Iterator[Param]:
        """Yield Param objects from the pattern string."""
        ...


class DefaultPatternLexer:
    """
    Tokenizes a command pattern string.

    Recognizes three token types:
      - Required parameters: enclosed in custom delimiters
      - Optional blocks: enclosed in custom delimiters

    Supports nested brackets using a stack.
    """

    def __init__(
        self,
        required_char: tuple[str, str] = ("<", ">"),
        optional_char: tuple[str, str] = ("[", "]"),
    ):
        """
        :required_char: A pair (open, close) for required parameters, e.g. ('<', '>').
        :optional_char: A pair (open, close) for optional blocks, e.g. ('[', ']').

        Raises:
            PatternLexerException: If any delimiter is not a single character.
        """
        if any(len(c) != 1 for c in required_char):
            raise PatternLexerException(
                "required_char delimiter must be a single character"
            )
        if any(len(c) != 1 for c in optional_char):
            raise PatternLexerException(
                "optional_char delimiter must be a single character"
            )

        self.required_char_open = required_char[0]
        self.required_char_close = required_char[1]
        self.optional_char_open = optional_char[0]
        self.optional_char_close = optional_char[1]

    def tokenize(self, pattern: str) -> Iterator[Param]:
        """
        List of param objects for each token in the pattern.

        Raises:
            PatternLexerException: If brackets are unbalanced or unclosed.
        """
        ptr = 0
        while ptr < len(pattern):
            c = pattern[ptr]
            if c.isspace():
                ptr += 1
                continue
            elif c == self.required_char_open:
                param, ptr = self._required_param(pattern, ptr)
                yield param
            elif c == self.optional_char_open:
                param, ptr = self._optional_param(pattern, ptr)
                yield param
            else:
                param, ptr = self._identifier_param(pattern, ptr)
                yield param

    def _bracket_matching(
        self, pattern: str, next_ptr: int, open_char: str, close_char: str
    ) -> int:
        """
        Return index of the matching closing bracket for the bracket starting at next_ptr-1.

        Raises:
            PatternLexerException: If brackets are unbalanced or unclosed.
        """
        ptr = next_ptr
        original_ptr = next_ptr - 1
        stack = [original_ptr]

        while ptr != len(pattern):
            c = pattern[ptr]
            if c == open_char:
                stack.append(ptr)
            elif c == close_char:
                if len(stack) == 0:
                    raise PatternLexerException("Unmatched closing bracket")
                stack.pop()
                if not stack:
                    return ptr
            ptr += 1
        raise PatternLexerException("Unclosed bracket")

    def _required_param(self, pattern: str, ptr: int) -> tuple[Param, int]:
        close_ptr = self._bracket_matching(
            pattern, ptr + 1, self.required_char_open, self.required_char_close
        )
        end_idx = close_ptr + 1
        return (
            Param(
                kind=ParamKind.Required,
                lexeme=pattern[ptr:end_idx],
                start=ptr,
                end=end_idx,
            ),
            end_idx,
        )

    def _optional_param(self, pattern: str, ptr: int) -> tuple[Param, int]:
        close_ptr = self._bracket_matching(
            pattern, ptr + 1, self.optional_char_open, self.optional_char_close
        )
        end_idx = close_ptr + 1
        return (
            Param(
                kind=ParamKind.Optional,
                lexeme=pattern[ptr:end_idx],
                start=ptr,
                end=end_idx,
            ),
            end_idx,
        )

    def _identifier_param(self, pattern: str, ptr: int) -> tuple[Param, int]:
        start = ptr
        while ptr < len(pattern) and not pattern[ptr].isspace():
            if pattern[ptr] in (self.required_char_open, self.optional_char_open):
                break
            if pattern[ptr] in (self.required_char_close, self.optional_char_close):
                raise PatternLexerException("Unmatched closing bracket")
            ptr += 1
        lexeme = pattern[start:ptr]
        return (
            Param(kind=ParamKind.Required, lexeme=lexeme, start=start, end=ptr),
            ptr,
        )
