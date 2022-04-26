# Relic

## Usage

```sh
# get all experiments where not all trials have 'finished': True
relic ls --metrics '(not (all (= finished True)))'

# get all experiments where any trials have 'finished': True
relic ls --metrics '(any (= finished True))'

# get all experiments where any trials have 'epochs' > 400
relic ls --metrics '(any (> epochs 400))'
```

## Development

Relic makes use of both static typing via `mypy` and unit testing.
