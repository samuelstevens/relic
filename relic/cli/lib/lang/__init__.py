from .... import experiments, types
from . import ast, lexing, parsing


def compile(code: str) -> ast.Expr:
    """
    Compiles code into a function.

    It is basically a mini-lisp.
    """
    tokens = lexing.Lexer(code).lex()
    chunk = parsing.Parser(tokens).parse()

    return chunk


def experiment(fn: ast.RuntimeFn) -> types.FilterFn[experiments.Experiment]:
    def execute(e: experiments.Experiment) -> bool:
        try:
            return bool(fn(e))
        except ast.RuntimeTypeError as err:
            print(err)
            return False

    return execute


def trial(fn: ast.RuntimeFn) -> types.FilterFn[experiments.Trial]:
    def execute(trial: experiments.Trial) -> bool:
        return bool(fn(trial))

    return execute


def needs_trials(expr: object) -> bool:
    if isinstance(expr, list):
        for value in expr:
            if needs_trials(value):
                return True

    if not isinstance(expr, ast.Expr):
        return False

    if (
        isinstance(expr, ast.Any)
        or isinstance(expr, ast.All)
        or (isinstance(expr, ast.Identifier) and expr.ident == "trialcount")
    ):
        return True

    for value in expr.__dict__.values():
        if needs_trials(value):
            return True

    return False
