# tests/lexer/test_pattern_lexer.py
import pytest
from mopplot.lexer.pattern_lexer import DefaultPatternLexer
from mopplot.lexer.token import ParamKind
from mopplot.exceptions import PatternLexerException


def test_basic_identifier():
    lexer = DefaultPatternLexer()
    tokens = list(lexer.tokenize("/give"))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Identifier
    assert tokens[0].lexeme == "/give"
    assert tokens[0].start == 0
    assert tokens[0].end == 5


def test_required_param():
    lexer = DefaultPatternLexer()
    tokens = list(lexer.tokenize("<player>"))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Required
    assert tokens[0].lexeme == "<player>"
    assert tokens[0].start == 0
    assert tokens[0].end == 8


def test_optional_param():
    lexer = DefaultPatternLexer()
    tokens = list(lexer.tokenize("[count]"))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Optional
    assert tokens[0].lexeme == "[count]"
    assert tokens[0].start == 0
    assert tokens[0].end == 7


def test_mixed_tokens():
    lexer = DefaultPatternLexer()
    pattern = "/give <player> <item> [count]"
    tokens = list(lexer.tokenize(pattern))
    expected = [
        (ParamKind.Identifier, "/give"),
        (ParamKind.Required, "<player>"),
        (ParamKind.Required, "<item>"),
        (ParamKind.Optional, "[count]"),
    ]
    assert len(tokens) == len(expected)
    for tok, (kind, lexeme) in zip(tokens, expected):
        assert tok.kind == kind
        assert tok.lexeme == lexeme


def test_whitespace_handling():
    lexer = DefaultPatternLexer()
    pattern = "  /give  \t <player>  "
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 2
    assert tokens[0].lexeme == "/give"
    assert tokens[1].lexeme == "<player>"


def test_nested_required():
    lexer = DefaultPatternLexer()
    pattern = "<a<b>>"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Required
    assert tokens[0].lexeme == "<a<b>>"


def test_nested_optional():
    lexer = DefaultPatternLexer()
    pattern = "[a[b]]"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Optional
    assert tokens[0].lexeme == "[a[b]]"


def test_empty_required():
    lexer = DefaultPatternLexer()
    pattern = "<>"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Required
    assert tokens[0].lexeme == "<>"


def test_empty_optional():
    lexer = DefaultPatternLexer()
    pattern = "[]"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 1
    assert tokens[0].kind == ParamKind.Optional
    assert tokens[0].lexeme == "[]"


def test_unclosed_required():
    lexer = DefaultPatternLexer()
    with pytest.raises(PatternLexerException, match="Unclosed bracket"):
        list(lexer.tokenize("<player"))


def test_unclosed_optional():
    lexer = DefaultPatternLexer()
    with pytest.raises(PatternLexerException, match="Unclosed bracket"):
        list(lexer.tokenize("[count"))


def test_unmatched_closing_bracket():
    lexer = DefaultPatternLexer()
    with pytest.raises(PatternLexerException, match="Unmatched closing bracket"):
        list(lexer.tokenize(">"))


def test_custom_delimiters():
    lexer = DefaultPatternLexer(required_char=("{", "}"), optional_char=("(", ")"))
    pattern = "/test {player} (optional)"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 3
    assert tokens[0].kind == ParamKind.Identifier
    assert tokens[0].lexeme == "/test"
    assert tokens[1].kind == ParamKind.Required
    assert tokens[1].lexeme == "{player}"
    assert tokens[2].kind == ParamKind.Optional
    assert tokens[2].lexeme == "(optional)"


def test_custom_identifier_kind():
    lexer = DefaultPatternLexer(
        required_char=("<", ">"),
        optional_char=("[", "]"),
        identifier_kind=ParamKind.Required,
    )
    tokens = list(lexer.tokenize("/give <player>"))
    assert tokens[0].kind == ParamKind.Required
    assert tokens[0].lexeme == "/give"
    assert tokens[1].kind == ParamKind.Required
    assert tokens[1].lexeme == "<player>"


def test_identifier_without_whitespace():
    lexer = DefaultPatternLexer()
    pattern = "give<player>"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 2
    assert tokens[0].lexeme == "give"
    assert tokens[1].lexeme == "<player>"


def test_multiple_whitespace():
    lexer = DefaultPatternLexer()
    pattern = "   /give     <player>   "
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 2
    assert tokens[0].lexeme == "/give"
    assert tokens[1].lexeme == "<player>"


def test_delimiter_single_char_validation():
    with pytest.raises(PatternLexerException, match="single character"):
        DefaultPatternLexer(required_char=("<<", ">>"))
    with pytest.raises(PatternLexerException, match="single character"):
        DefaultPatternLexer(optional_char=("[[", "]]"))


def test_empty_string():
    lexer = DefaultPatternLexer()
    tokens = list(lexer.tokenize(""))
    assert tokens == []


def test_only_whitespace():
    lexer = DefaultPatternLexer()
    tokens = list(lexer.tokenize("   \t\n "))
    assert tokens == []


def test_identifier_contains_delimiter_characters():
    lexer = DefaultPatternLexer()
    pattern = "a<b>c"
    tokens = list(lexer.tokenize(pattern))
    assert len(tokens) == 3
    assert tokens[0].lexeme == "a"
    assert tokens[1].lexeme == "<b>"
    assert tokens[2].lexeme == "c"
