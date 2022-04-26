import dataclasses
import string
from typing import Iterable, List, Tuple

import preface


class TType(preface.SumType):
    EOF = "eof"
    # keywords
    Any = "any"
    All = "all"
    Or = "or"
    And = "and"
    Not = "not"
    Like = "like"
    Len = "len"
    Sum = "sum"
    # user value
    Identifier = "ident"
    Number = "num"
    Boolean = "bool"
    Nil = "NoneType"
    String = "str"
    Regex = "re"
    # parens
    LeftParen = "("
    RightParen = ")"
    # comparisons
    Greater = ">"
    GreaterEqual = ">="
    Less = "<"
    LessEqual = "<="
    Equal = "=="
    # symbols
    Minus = "-"
    Period = "."
    Slash = "/"
    Star = "*"


KEYWORD_LOOKUP = {
    "any": TType.Any,
    "all": TType.All,
    "or": TType.Or,
    "and": TType.And,
    "not": TType.Not,
    "like": TType.Like,
    "len": TType.Len,
    "sum": TType.Sum,
    "True": TType.Boolean,
    "False": TType.Boolean,
    "None": TType.Nil,
}

SYMBOL_LOOKUP = {
    "(": TType.LeftParen,
    ")": TType.RightParen,
    ".": TType.Period,
    "~": TType.Like,
    "/": TType.Slash,
    "*": TType.Star,
}


@dataclasses.dataclass
class Token:
    ttype: TType
    literal: str
    pos: int


def EOF(pos: int) -> Token:
    return Token(TType.EOF, "eof", pos)


class Lexer:
    def __init__(self, code: str) -> None:
        self.pos = 0
        self.code = code
        self.context = ""

    def at_end(self) -> bool:
        return self.pos >= len(self.code)

    def advance(self) -> Tuple[str, int]:
        pos = self.pos
        self.pos += 1
        return self.code[pos], pos

    def _match(self, expected: str) -> bool:
        if self.at_end():
            return False

        if self.code[self.pos] != expected:
            return False

        self.pos += 1
        return True

    def peek(self) -> str:
        if self.at_end():
            return ""

        return self.code[self.pos]

    def _scan_token(self) -> Token:
        while not self.at_end():
            ch, pos = self.advance()
            if ch in string.whitespace:
                continue

            if ch in SYMBOL_LOOKUP:
                return Token(SYMBOL_LOOKUP[ch], ch, pos)

            # comparisons
            if ch == ">":
                return (
                    Token(TType.GreaterEqual, ">=", pos)
                    if self._match("=")
                    else Token(TType.Greater, ">", pos)
                )
            if ch == "<":
                return (
                    Token(TType.LessEqual, "<=", pos)
                    if self._match("=")
                    else Token(TType.Less, "<", pos)
                )

            if ch == "=" and self._match("="):
                return Token(TType.Equal, "==", pos)

            # literals
            if ch in string.ascii_letters:
                return lex_word(self, ch)

            if ch in string.digits:
                return lex_num(self, ch)

            if ch == "'":
                return lex_str(self, ch)

            if ch == "|":
                return lex_regex(self, ch)

            raise LexError(self, ch)

        raise LexError(self, "EOF")

    def _lex(self) -> Iterable[Token]:
        while not self.at_end():
            yield self._scan_token()

        yield EOF(self.pos)

    def lex(self) -> List[Token]:
        return list(self._lex())


def lex_num(lexer: Lexer, start: str) -> Token:
    assert start in string.digits

    pos = lexer.pos - 1

    letters = [start]

    while not lexer.at_end() and lexer.peek() in string.digits:
        ch, _ = lexer.advance()
        letters.append(ch)

    return Token(TType.Number, "".join(letters), pos)


def lex_word(lexer: Lexer, start: str) -> Token:
    assert start in string.ascii_letters

    pos = lexer.pos - 1

    letters = [start]

    valid_characters = string.ascii_letters + "._-" + string.digits

    while not lexer.at_end() and lexer.peek() in valid_characters:
        ch, _ = lexer.advance()
        letters.append(ch)

    word = "".join(letters)
    if word in KEYWORD_LOOKUP:
        return Token(KEYWORD_LOOKUP[word], word, pos)

    return Token(TType.Identifier, word, pos)


def lex_str(lexer: Lexer, start: str) -> Token:
    assert start == "'"

    pos = lexer.pos - 1

    contents = []

    while not lexer.at_end() and lexer.peek() != "'":
        ch, _ = lexer.advance()
        contents.append(ch)

    lexer.advance()  # consume the ' character.

    if lexer.at_end():
        raise LexError(lexer, "EOF")

    return Token(TType.String, "".join(contents), pos)


def lex_regex(lexer: Lexer, start: str) -> Token:
    assert start == "|"

    pos = lexer.pos - 1

    contents = []

    while not lexer.at_end() and lexer.peek() != "|":
        ch, _ = lexer.advance()
        contents.append(ch)

    lexer.advance()  # consume the / character.

    if lexer.at_end():
        raise LexError(lexer, "EOF")

    return Token(TType.Regex, "".join(contents), pos)


class LexError(Exception):
    pos: int
    ch: str
    code: str
    context: str

    def __init__(self, lexer: Lexer, ch: str):
        self.pos = lexer.pos - 1
        self.ch = ch
        self.code = lexer.code
        self.context = lexer.context
        self.message = f"Error while tokenizing. Unexpected character '{ch}'\n\n\t{self.code}\n\t{' '*self.pos}^\nContext: {self.context}"

    def __str__(self) -> str:
        return self.message
