"""
Recursive descent parser for language.
"""
from typing import Any, List, Union

from . import ast
from .lexing import EOF, Token, TType


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.depth = 0

    def _at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def advance(self) -> Token:
        val = self.tokens[self.pos]
        self.pos += 1
        return val

    def match(self, ttype: TType) -> bool:
        if self._at_end():
            return False

        if self.tokens[self.pos].ttype != ttype:
            return False

        self.pos += 1
        return True

    def match_or_error(self, ttypes: Union[TType, List[TType]]) -> Token:
        next_ttype = self.peek().ttype
        if isinstance(ttypes, list) and next_ttype not in ttypes:
            raise ParseError(self, ttypes)

        elif isinstance(ttypes, TType) and next_ttype is not ttypes:
            raise ParseError(self, [ttypes])

        return self.advance()

    def peek(self) -> Token:
        if self._at_end():
            return EOF(self.pos)

        return self.tokens[self.pos]

    def parse(self) -> ast.Expr:
        token = self.advance()

        if token.ttype is TType.LeftParen:
            token = self.advance()  # skip left paren
            table = FN_PARSE_TABLE
        else:
            table = LITERAL_PARSE_TABLE  # type: ignore

        if token.ttype not in table:
            raise ParseError(self, list(table.keys()))

        parselet, cls = table[token.ttype]

        return parselet(self, token, cls)


def parse_number(parser: Parser, token: Token, cls: Any) -> ast.Number:
    # NUM -> DIGIT+ | DIGIT+ . DIGIT+
    digits = token.literal
    if parser.match(TType.Period):
        if parser.peek().ttype is TType.Number:
            fractions = parser.advance().literal
            return ast.Number(float(digits) + float(f".{fractions}"))
        else:
            raise ParseError(parser, [TType.Number])
    return ast.Number(float(digits))


def parse_one_arg_fn(parser: Parser, token: Token, cls: Any) -> ast.Expr:
    expr = parser.parse()
    parser.match_or_error([TType.RightParen])

    return cls(expr)  # type: ignore


def parse_two_arg_fn(parser: Parser, token: Token, cls: Any) -> ast.Expr:
    left = parser.parse()
    right = parser.parse()

    parser.match_or_error([TType.RightParen])

    return cls(left, right)  # type: ignore


def parse_variadic_arg_fn(parser: Parser, token: Token, cls: Any) -> ast.Expr:
    args = []
    while not parser.peek().ttype == TType.RightParen:
        args.append(parser.parse())

    assert len(args) > 0

    parser.match_or_error([TType.RightParen])

    return cls(args)  # type: ignore


def parse_identifier(parser: Parser, token: Token, cls: object) -> ast.Identifier:
    return ast.Identifier(token.literal)


def parse_boolean(parser: Parser, token: Token, cls: object) -> ast.Boolean:
    if token.literal == "True":
        return ast.Boolean(True)
    elif token.literal == "False":
        return ast.Boolean(False)
    else:
        raise ParseError(parser, [TType.Boolean])


def parse_none(parser: Parser, token: Token, cls: object) -> ast.Nil:
    if token.literal == "None":
        return ast.Nil()
    else:
        raise ParseError(parser, [TType.Boolean])


def parse_string(parser: Parser, token: Token, cls: object) -> ast.String:
    return ast.String(token.literal)


def parse_regex(parser: Parser, token: Token, cls: object) -> ast.Regex:
    return ast.Regex(token.literal)


FN_PARSE_TABLE = {
    # variadic args
    TType.And: (parse_variadic_arg_fn, ast.And),
    TType.Or: (parse_variadic_arg_fn, ast.Or),
    # two args
    TType.Equal: (parse_two_arg_fn, ast.Equal),
    TType.Less: (parse_two_arg_fn, ast.Less),
    TType.LessEqual: (parse_two_arg_fn, ast.LessEqual),
    TType.Greater: (parse_two_arg_fn, ast.Greater),
    TType.GreaterEqual: (parse_two_arg_fn, ast.GreaterEqual),
    TType.Like: (parse_two_arg_fn, ast.Like),
    TType.Slash: (parse_two_arg_fn, ast.Divide),
    # one arg
    TType.Not: (parse_one_arg_fn, ast.Not),
    TType.All: (parse_one_arg_fn, ast.All),
    TType.Any: (parse_one_arg_fn, ast.Any),
    TType.Len: (parse_one_arg_fn, ast.Len),
    TType.Sum: (parse_one_arg_fn, ast.Sum),
}


LITERAL_PARSE_TABLE = {
    TType.Number: (parse_number, ast.Number),
    TType.Identifier: (parse_identifier, ast.Identifier),
    TType.Boolean: (parse_boolean, ast.Boolean),
    TType.String: (parse_string, ast.String),
    TType.Regex: (parse_regex, ast.Regex),
    TType.Nil: (parse_none, ast.Nil),
}


class ParseError(Exception):
    pos: int
    token: Token
    tokens: List[Token]
    expected: List[TType]

    def __init__(self, parser: Parser, expected: List[TType]):
        self.pos = parser.pos
        self.token = parser.peek()
        self.tokens = parser.tokens
        self.expected = expected

        token_stream_str = " ".join(token.literal for token in self.tokens)
        token_stream_marker = " ".join(
            "^" + " " * (len(token.literal) - 1)
            if i == self.pos
            else " " * len(token.literal)
            for i, token in enumerate(self.tokens)
        )

        self.message = f"Error while parsing.\nUnexpected token '{self.token.literal}' ({self.token.ttype})\n\n\t{token_stream_str}\n\t{token_stream_marker}\n\nExpected one of {expected}"

    def __str__(self) -> str:
        return self.message


class EndOfStreamError(ParseError):
    def __str__(self) -> str:
        return f"Error while parsing.\nUnexpected end of stream. Expected one of {self.expected}."
