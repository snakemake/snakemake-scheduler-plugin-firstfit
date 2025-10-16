
### Why this Plugin

Even though `snakemake`'s default schedulers are fast enough for the majority of workflows, for very large workflows (i.e. > 300k jobs) they can be considerably slow. This is because, every time a job finishes, `snakemake` needs to re-evaluate all pending jobs to select the subset that maximizes usage of available resources. This can be specially problematic if the workflow has a lot of relatively fast jobs, since the time lost waiting for the scheduler could have been used to process jobs instead.

`snakemake` is aware of this and, if the default `ilp` scheduler takes more than 10s, it automatically switches to the `greedy` scheduler. However, it is known that the `ilp` sometimes ignores the timeout (coin-or/Cbc#487) and that it can be quite slow instantiating large problems (coin-or/pulp#749).

`firstfit` aims to considerably speed-up the scheduling process by simplifying the optimization steps (and sacrificing some resource efficiency). On a very simple example workflow with ~600k jobs, `snakemake`'s `greedy` scheduler takes around 90s for each scheduling round (i.e. between a job finishing and the launching of the next batch of jobs). `firstfit`, on the other hand, takes between ~5s (greediness of 1) and 1s (greediness of 0).

### How this Plugin works

In this plugin, jobs are selected for run in a [first-fit with one bin](https://en.wikipedia.org/wiki/First-fit_bin_packing) way. Briefly, available jobs are sorted by their `reward` (so that higher-reward jobs are evaluated first), and sequentially submited as long as there are available resources.

### Contributions

We welcome bug reports, feature requests, and pull requests!
Please report issues specific to this plugin [in the plugin's GitHub repository](https://github.com/snakemake/snakemake-scheduler-plugin-firstfit/issues).

### Configuration

Snakemake offers great [capabilities to specify and thereby limit resources](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#resources) used by a workflow as a whole and by individual jobs.
