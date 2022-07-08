# Introduction to Relic

Relic has two main components. 
First is the Python package, used to record experiments in Relic.
For example:

```python

import relic

experiment_config = {'learning_rate': 1e-5}

experiment = relic.new_experiment(experiment_config)

for batch in data:
    # do some training
    ...

model.save(saved_model_path)

experiment.update_trial(metric_dict, saved_model_path)
```

The second main component is the Relic command-line interface.

If you ran lots of experiments, with lots of different `experiment_configs`, you might be interested in getting a high level overview of the results.

For example

```
$ relic ls --show succeeded
experiment      trials  training.clipping.algorithm      training.clipping.value  succeeded  
------------  --------  -----------------------------  -------------------------  -----------
0d1c904b12           1  -                                                  0      0/1 (0%)   
0d5b20416e           3  norm                                               5e+05  3/3 (100%) 
```

This example shows that without clipping (first row), none of my trials succeeded (0/1).
When I added clipping, 3/3 of trials succeeded.

The real power of the `relic` command is the filtering you can do to further drill down into your experimental results without needing to start a Jupyter notebook (which is also well-supported by relic).

The filtering language is explained in more detail in [the language docs](lang/intro.md), but I will show a couple examples to (hopefully) convince you of its utility.

1. Show experiments with a learning rate in a range and a given clipping value:

```
relic ls --experiments "(and (< training.learning_rate 0.0005) (> training.learning_rate 0.00001))" "(== training.clipping.value 0.0005)"
```

2. Show experiments with any trials that finished but didn't converge:

```
relic ls --experiments "(any (and finished (not converged)))"
```

3. Show experiments that failed on every trial with a dataset matching the regular expression `images/.*/birds`:

```
relic ls --experiments "(all (not converged))" "(like data.source |images/.*/birds|)"
```

Again, the full language is explained in [the language docs](lang/intro.md).
