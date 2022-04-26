# Merging

How can we effectively merge experiments from two directories?

1. Do not allow trials to be updated.
2. Give trials a special field "finished", and an unfinished trial can be replaced by a finished trial.
3. Treat the experiment directory as a git repository and use git to merge trials.
4. Find out how git merges work and just implement them myself.
5. Look into CRDTs and apply them to this problem.
