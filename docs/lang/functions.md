# Functions

This page documents all of the built-in functions in the Relic query language.

The file `relic/cli/lib/lang/ast.py` has the source code for all of these functions.

## Or

Name: or

Arguments: List of expressions that evaluate to bools. 

Notes: Short-circuits evaluation. As soon as one argument evaluates to True, stops evaluating the others.

Example: `(or (< model.size 100) (== model.size 100))`

## And

Name: and
