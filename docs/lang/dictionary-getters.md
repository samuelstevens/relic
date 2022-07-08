# Dictionary Getters

Dictionary getters are a special catch-all expression in Relic that progressively index into nested dictionaries until it reaches a value or the key doesn't exist.

For example, suppose the config you pass to `relic.new_experiment` is:

```python
config = {
    'training': {
        'learning_rate': 1e-5,
        'epochs': 30,
        'clipping': {
            'variety': None,
            'value': 0.0,
        }
    },
    'model': {
        'model_name': 'gpt2',
        'dropout': 0.1,
    },
    'trials': 10,
}
```

Then the expression `training.clipping.variety` evaluates to `None`, the expression `model.dropout` evaluates to `0.1` and the expression `trials` evaluates to `10`.

The expression `model.name` evaluates to `None` **because there is no key `name` in `model`.**
This is useful because your configs might have different keys, and you want to find all experiments without, say, `training.clipping`. Then you can use `(== training.clipping None)` to do that.

## What Gets Evaluated as a Getter?

Anything that is not a built-in function or literal is evaluated as a getter.

## Special Getters

`experimenthash` is a special getter that evaluates to the experiment's hash as a string.

`trialcount` is a special getter that evaluates to the number of trials as an int.
