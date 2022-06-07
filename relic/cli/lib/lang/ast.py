import functools
import operator
import re
from typing import Callable, List, Union

import preface
from typing_extensions import TypeGuard

from ....experiments import Experiment, Trial
from .. import logging

RuntimeObj = Union[Trial, Experiment, float, int, bool, str, None]

RuntimeFn = Callable[[RuntimeObj], RuntimeObj]

number = Union[float, int]


class RuntimeTypeError(TypeError):
    pass


def isnumber(obj: object) -> TypeGuard[number]:
    if isinstance(obj, bool):
        return False

    if isinstance(obj, int):
        return True

    if isinstance(obj, float):
        return True

    return False


def isnumberlist(obj: object) -> TypeGuard[List[number]]:
    if not isinstance(obj, list):
        return False

    for o in obj:
        if not isnumber(o):
            return False

    return True


def isresult(obj: object) -> TypeGuard[Union[number, bool, str, None]]:
    if isnumber(obj):
        return True

    if isinstance(obj, bool):
        return True

    if isinstance(obj, str):
        return True

    if obj is None:
        return True

    return False


class Expr:
    def __call__(self, arg: RuntimeObj) -> RuntimeObj:
        ...


class Or(Expr):
    def __init__(self, exprs: List[Expr]) -> None:
        self.exprs = exprs

    def __call__(self, arg: RuntimeObj) -> bool:
        result = False
        for expr in self.exprs:
            # Logical short-circuiting is required. We can't do
            #     result = result or expr(arg)
            # because we need to type-check expr(arg).
            if result:
                break

            expr_result = expr(arg)
            if not isinstance(expr_result, bool):
                raise TypeError()
            result = result or expr_result

        return result

    def __repr__(self) -> str:
        return f"(or {' '.join(map(str, self.exprs))})"


class And(Expr):
    return_type = bool

    def __init__(self, exprs: List[Expr]) -> None:
        self.exprs = exprs

    def __call__(self, arg: RuntimeObj) -> bool:
        result = True
        for expr in self.exprs:
            # Logical short-circuiting is required. We can't do
            #     result = result and expr(arg)
            # because we need to type-check expr(arg).
            if not result:
                break

            expr_result = expr(arg)
            if not isinstance(expr_result, bool):
                raise TypeError()
            result = result and expr_result

        return result


class NumericalCompare(Expr):
    def __init__(
        self,
        left: Expr,
        right: Expr,
        comparison: Callable[[float, float], bool],
    ) -> None:
        self.left = left
        self.right = right
        self.comparison = comparison

    def __call__(self, arg: RuntimeObj) -> bool:
        left_val = self.left(arg)
        if not isnumber(left_val):
            raise RuntimeTypeError(
                f"In the expression {self}, left expression {self.left}({arg}) must be a number, not {type(left_val)}!"
            )

        right_val = self.right(arg)
        if not isnumber(right_val):
            raise RuntimeTypeError(
                f"In the expression {self}, right expression {self.right}({arg}) must be a number, not {type(right_val)}!"
            )

        return self.comparison(left_val, right_val)

    def __repr__(self) -> str:
        return f"({self.comparison} {self.left} {self.right})"


Greater = functools.partial(NumericalCompare, comparison=operator.gt)
GreaterEqual = functools.partial(NumericalCompare, comparison=operator.ge)
Less = functools.partial(NumericalCompare, comparison=operator.lt)
LessEqual = functools.partial(NumericalCompare, comparison=operator.le)


class Number(Expr):
    def __init__(self, number: number) -> None:
        self.number = number

    def __repr__(self) -> str:
        return str(self.number)

    def __call__(self, arg: RuntimeObj) -> number:
        return self.number


class Identifier(Expr):
    def __init__(self, ident: str) -> None:
        self.ident = ident

    def __call__(self, arg: RuntimeObj) -> Union[str, number, bool, None]:
        if isinstance(arg, Experiment):
            if self.ident == "trialcount":
                return len(arg)
            if self.ident == "experimenthash":
                return arg.hash
            if not preface.dict.contains(arg.config, self.ident):
                if "experiment" in self.ident:
                    logging.warn(
                        "Did you mean 'experimenthash' instead of '%s'?", self.ident
                    )
                return None
            return preface.dict.get(arg.config, self.ident)  # type: ignore
        elif isinstance(arg, dict):
            if not preface.dict.contains(arg, self.ident):
                return False
            return preface.dict.get(arg, self.ident)  # type: ignore
        else:
            raise TypeError()

    def __repr__(self) -> str:
        return self.ident


class String(Expr):
    def __init__(self, string: str) -> None:
        self.string = string

    def __call__(self, arg: RuntimeObj) -> str:
        return self.string

    def __repr__(self) -> str:
        return f"'{self.string}'"


class Boolean(Expr):
    def __init__(self, boolean: bool) -> None:
        self.boolean = boolean

    def __call__(self, arg: RuntimeObj) -> bool:
        return self.boolean

    def __repr__(self) -> str:
        return str(self.boolean)


class Nil(Expr):
    def __init__(self) -> None:
        pass

    def __call__(self, arg: RuntimeObj) -> RuntimeObj:
        return None

    def __repr__(self) -> str:
        return "None"


class Regex(Expr):
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def __call__(self, arg: RuntimeObj) -> str:
        return self.pattern

    def __repr__(self) -> str:
        return f"|{self.pattern}|"


class Equal(Expr):
    def __init__(self, left: Expr, right: Expr) -> None:
        self.left = left
        self.right = right

    def __call__(self, arg: RuntimeObj) -> bool:
        return self.left(arg) == self.right(arg)

    def __repr__(self) -> str:
        return f"( == {self.left} {self.right} )"


class Like(Expr):
    def __init__(self, expr: Expr, regex: Expr) -> None:
        if not isinstance(regex, Regex):
            raise TypeError(
                f"Expression {regex} must be a regular expression, not {type(regex)}!"
            )

        self.expr = expr
        # For performance optimizations, we cache the regex pattern so it doesn't need to be parsed each time the Like expression is called.
        self.regex = re.compile(regex("dummy"))

    def __call__(self, arg: RuntimeObj) -> bool:
        value = str(self.expr(arg))

        return bool(self.regex.search(value))

    def __repr__(self) -> str:
        return f"( like {self.expr} {self.regex} )"


class Not(Expr):
    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def __call__(self, arg: RuntimeObj) -> bool:
        result = self.expr(arg)

        if not isinstance(result, bool):
            raise TypeError(f"Cannot 'not' {result} of expression {self.expr}!")

        return not result

    def __repr__(self) -> str:
        return f"( not {self.expr} )"


class Len(Expr):
    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def __call__(self, arg: RuntimeObj) -> int:
        result = self.expr(arg)

        try:
            # It's ok to call type: ignore because we want type
            # errors to bubble up. The relic language is duck-typed.
            return len(result)  # type: ignore
        except TypeError:
            raise TypeError(
                f"Result {result} of expression {self.expr} does not have a length!"
            )

    def __repr__(self) -> str:
        return f"( len {self.expr} )"


class Sum(Expr):
    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def __call__(self, arg: RuntimeObj) -> number:
        result = self.expr(arg)

        try:
            # It's ok to call type: ignore because we want type errors to bubble up. The relic language is duck-typed.
            return sum(result)  # type: ignore
        except TypeError:
            raise TypeError(f"Cannot sum {result} of expression {self.expr}!")

    def __repr__(self) -> str:
        return f"( sum {self.expr} )"


class Divide(Expr):
    def __init__(self, dividend: Expr, divisor: Expr) -> None:
        self.dividend = dividend
        self.divisor = divisor

    def __repr__(self) -> str:
        return f"( / {self.dividend} {self.divisor} )"

    def __call__(self, arg: RuntimeObj) -> float:
        dividend = self.dividend(arg)
        if not isnumber(dividend):
            raise TypeError()

        divisor = self.divisor(arg)
        if not isnumber(divisor):
            raise TypeError(
                f"Expected divisor {divisor} in {self} to be a number, not {type(divisor)}!"
            )

        return dividend / divisor


class Any(Expr):
    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def __call__(self, arg: RuntimeObj) -> bool:
        if not isinstance(arg, Experiment):
            raise TypeError()

        result = False
        for trial in arg:
            trial_result = self.expr(trial)
            if not isinstance(trial_result, bool):
                raise TypeError()
            result = result or trial_result
        return result

    def __repr__(self) -> str:
        return f"( any {self.expr} )"


class All(Expr):
    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def __call__(self, arg: RuntimeObj) -> bool:
        if not isinstance(arg, Experiment):
            raise TypeError()

        result = True
        for trial in arg:
            trial_result = self.expr(trial)
            if not isinstance(trial_result, bool):
                raise TypeError()
            result = result and trial_result
        return result

    def __repr__(self) -> str:
        return f"( all {self.expr} )"
