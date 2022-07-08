# Functions

This page documents all of the built-in functions in the Relic query language.

The file `relic/cli/lib/lang/ast.py` has the source code for all of these functions.

These functions are listed alphabetically. 
Semantically-related functions link to each other.

## All

Name: any

Arguments: A single expression that, given a trial, evaluates to a bool.

Returns: True if the expression evaluates to True for all trials. False otherwise.

Notes: All expressions are given a trial as an argument, *not* an experiment's config. So [dictionary getters](dictionary-getters.md) look inside the trial dict for keys. Related to [Any](#any).

Example: `(all finished)`

## And

Name: and

Arguments: List of expressions that evaluate to bools. 

Returns: True if every argument is True, otherwise False.

Notes: Short-circuits evaluation. As soon as one argument evaluates to False, stops evaluating the others. Most of the time, you don't need `and` because arguments provided to `--experiments` (and other commands) are automatically "and-ed" together.Related to [Or](#or).

Example: `(and finished succeeded)`

## Any

Name: any

Arguments: A single expression that, given a trial, evaluates to a bool.

Returns: True if the expression evaluates to True for at least one trial. False otherwise.

Notes: All expressions are given a trial as an argument, *not* an experiment's config. So [dictionary getters](dictionary-getters.md) look inside the trial dict for keys. Related to [All](#all).

Example: `(any (not finished))`

## / (Divide)

Name: `/`

Arguments: Two expressions that evaluate to numbers.

Returns the first argument divided by the second argument as a float.

Notes: I use this with [Sum](#sum) to calculate means.

Example: `(/ epochs trialcount)`

## == (Equals)

Name: ==

Arguments: two expressions that evaluate to any type.

Returns: True if the expressions are equal, False otherwise.

Notes: There are no type restrictions, but no type coercing happens either.

Example: `(== model.name 'gpt2')`

## Length

Name: len

Arguments: One argument that evaluates to any expression with a length in Python. This includes lists, dictionaries, and strings.

Returns: The argument's length.

Notes: If the expression does not have a length, it will throw a type error.

Example: `(len training_losses)`

## ~ (Like)

Name: `like` or `~`

Arguments: An expression that evaluates to any type and a [regular expression](literals.md#regular-expressions).

Returns: True if there is at least one match, False otherwise.

Notes: The first argument will be converted to a string using Python's `str` function. So you can write regular expressions to match against lists, dictionaries, etc. You just have to be aware of what the resulting string will look like. 

Example: `(~ model.name |gpt2(:?-.*)?|)`


## Not

Name: `not`

Arguments: One expression that evaluates to a bool.

Returns: The inverse of the expression (True if False, False if True).

Example: `(not succeeded)`


## \< \> \<= \>= (Numerical Comparisons)

Name: `<` `>` `<=` `>=`

Arguments: two expressions that both evaluate to numbers.

Returns: True or False depending on the comparison.

Notes: The first argument goes on the left side of the function "name". So `(< 4 5)` checks whether 4 < 5.

Example: `(<= model.size 100)`

## Or

Name: or

Arguments: List of expressions that evaluate to bools.

Returns: True if any arguments are True, otherwise False.

Notes: Short-circuits evaluation. As soon as one argument evaluates to True, stops evaluating the others. Related to [And](#and).

Example: `(or (< model.size 100) (== model.size 100))`

## Sum

Name: sum

Arguments: One argument that is list-like and can be summed. 

Returns: The argument's sum.

Notes: This function evaluates its argument, then calls the Python built-in `sum()`. If the evaluated argument causes a type-error, then this throws an error as well. I mostly use this with [`/` (divide)](#-divide) to calculate means and use them in my queries.
