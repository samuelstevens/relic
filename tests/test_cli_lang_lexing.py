import pytest

from relic.cli.lib.lang.lexing import Lexer, LexError, Token, TType


def test_lex_smoke1() -> None:
    code = "(<= trials 3)"
    list(Lexer(code).lex())


def test_lex_smoke2() -> None:
    code = "(all (== trials 3))"
    list(Lexer(code).lex())


def test_lex_smoke3() -> None:
    code = "(not (any (== trials 3)))"
    list(Lexer(code).lex())


def test_lex_smoke4() -> None:
    code = "(not (any (== dropout 0.0)))"
    list(Lexer(code).lex())


def test_lex_smoke5() -> None:
    code = "(not (any (== file 'a')))"
    list(Lexer(code).lex())


def test_lex_error1() -> None:
    code = "(not &)"

    with pytest.raises(LexError):
        list(Lexer(code).lex())


def test_lex_returns_tokens1() -> None:
    code = "(>= or)"
    expected = [
        Token(TType.LeftParen, "(", 0),
        Token(TType.GreaterEqual, ">=", 1),
        Token(TType.Or, "or", 4),
        Token(TType.RightParen, ")", 6),
        Token(TType.EOF, "eof", 7),
    ]

    actual = list(Lexer(code).lex())

    assert actual == expected


def test_lex_returns_tokens2() -> None:
    code = "(>= epochs 100)"
    expected = [
        Token(TType.LeftParen, "(", 0),
        Token(TType.GreaterEqual, ">=", 1),
        Token(TType.Identifier, "epochs", 4),
        Token(TType.Number, "100", 11),
        Token(TType.RightParen, ")", 14),
        Token(TType.EOF, "eof", 15),
    ]

    actual = list(Lexer(code).lex())

    assert actual == expected
