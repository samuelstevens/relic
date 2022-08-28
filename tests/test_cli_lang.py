from relic.cli.lib.lang import compile, needs_trials


def test_needs_trials() -> None:
    expr = compile("(any (not finished))")

    assert needs_trials(expr)


def test_doesnt_needs_trials() -> None:
    expr = compile("(not (not normalized))")

    assert not needs_trials(expr)


def test_needs_trials_nested() -> None:
    expr = compile("(not (or (any finished) normalized))")

    assert needs_trials(expr)


def test_needs_trials_nested_sum() -> None:
    expr = compile("(not (sum (any epochs)))")

    assert needs_trials(expr)
