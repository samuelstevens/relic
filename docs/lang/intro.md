# Relic Language

The Relic query language is used to filter experiments and trials.
It has a lisp-like syntax (because that was easiest to write a parser for).
It tries to be regular so that you can compose it in ways that were not planned for, and it should just work.

At a high level there are three main components:

1. [Literals](literals) like `None`, `0.0001`, and `'gpt2'`.
2. [Dictionary getters](dictionary-getters) like `training.clipping.value` and `succeeded`
3. [Functions](functions) like `all`, `and`, and `like`.

These three components form expressions.
I will give some examples of expressions and how they evaluate.

First, an expression that checks whether an experiment's config has a given value:

```
(== training.clipping.value 0.0005)
 ^  ^                       ^
 |  |                       evaluates to 0.0005.
 |  |
 Equals function returns True or False based on whether the function arguments are equal.
    |
    Checks if the experiment's config contains a key 'training'. Checks if the value has a key 'clipping', then if that has a key 'value'. If any of those keys are missing, evaluates to None. If the keys are all present, returns the value stored.
```

If an experiment's `config['training']['clipping']['value'] = 0.0005`, then this expression evaluates to `True`. 

Second, an expression that checks if the experiment has any trials that took longer than 100 epochs:

```
(any (> epochs 100))
 ^    ^ ^      ^
 |    | |      Evaluates to 100.
 |    | |
 For each trial in an experiment, checks if the argument is True. If *any* of the expressions evaluate to True, the entire expression is True.
      | |
      | Checks for the trial's 'epochs' key and returns the value, if it exists.
      |
      Returns if the first argument is greater than the second argument.
```
