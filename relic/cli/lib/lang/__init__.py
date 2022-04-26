from .... import experiments, types
from . import ast, lexing, parsing


def compile(code: str) -> ast.RuntimeFn:
    """
    Compiles code into a function.

    It is basically a mini-lisp.
    """
    tokens = lexing.Lexer(code).lex()
    chunk = parsing.Parser(tokens).parse()

    return chunk


def experiment(code: str) -> types.FilterFn[experiments.Experiment]:
    chunk = compile(code)

    def execute(e: experiments.Experiment) -> bool:
        try:
            return bool(chunk(e))
        except ast.RuntimeTypeError as err:
            print(err)
            return False

    return execute


def trial(code: str) -> types.FilterFn[experiments.Trial]:
    chunk = compile(code)

    def execute(trial: experiments.Trial) -> bool:
        return bool(chunk(trial))

    return execute
