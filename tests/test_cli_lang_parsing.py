from relic.cli.lib.lang.lexing import Lexer
from relic.cli.lib.lang.parsing import Parser


def test_parse_experiment_smoke1() -> None:
    code = "(any (== epochs 1000 ))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke2() -> None:
    code = "(all (> epochs 100))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke3() -> None:
    code = "(all (and (< epochs 1000) (> epochs 100)))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke4() -> None:
    code = "(all (< epochs 100))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke5() -> None:
    code = "(any (and (== finished True) (== succeeded True)))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke6() -> None:
    code = "(all (not (== batch_size 1)))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke7() -> None:
    code = "(all (not (like batch_size |^1$|)))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke8() -> None:
    code = "(== trialcount 3)"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_experiment_smoke9() -> None:
    code = "(like experimenthash |abcde|)"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_trial_smoke1() -> None:
    code = "(not (== batch_size 1))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None


def test_parse_trial_smoke2() -> None:
    code = "(not (> epochs 100.5))"
    tokens = Lexer(code).lex()
    ast = Parser(tokens).parse()

    assert ast is not None
