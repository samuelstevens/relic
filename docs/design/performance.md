# Performance

# 08/28/2022

I am going to split configs and trials up to speed up `relic ls`.

The new directory structure will be:

```
relics/
  project.json
  v1/
    ffe1bc1d0f45f9c3988683599c2ff71eba28fab3/
      config
      trials/
        0.trial
        1.trial
        2.trial
        3.trial
      models/
        0.model
        1.model
        2.model
        3.model
```

So the changes will be:

1. Remove models directory from root.
2. Store configs in `<hash>.config` files and trials in `<hash>/0.trial` files.
3. (Optional) Change models to be stored in 0.model, 1.model, etc.
4. Write a migration script.

### Language/AST

To *not* need to load the trials for `relic ls`, we need to make sure there are no `Any` or `All` nodes in the AST because they are the only ones that reference trials.

### Migration Script

The current structure is:

```
relics/
  project.json
  v1/
    ffe1bc1d0f45f9c3988683599c2ff71eba28fab3.relic
    models/
      ffe1bc1d0f45f9c3988683599c2ff71eba28fab3/
        trial_0.trial
        trial_1.trial
        trial_2.trial
        trial_3.trial
```

I need to move it to this:

```
relics/
  project.json
  v1/
    ffe1bc1d0f45f9c3988683599c2ff71eba28fab3/
      config
      trials/
        0.trial
        1.trial
        2.trial
        3.trial
      models/
        0.model
        1.model
        2.model
        3.model
```

To do this, in pseudocode (python)

```python
mv v1 v1-old
for hash in v1-old:
    mkdir v1/hash
    mkdir v1/hash/trials
    mv v1/models/hash v1/hash/models

    for model in v1/hash/models:
        mv model MODEL.model

    config, trials = read v1-old/hash

    write config to v1/hash/config
    for trial in trials:
        write trial to v1/hash/trials/TRIAL.trial
```
