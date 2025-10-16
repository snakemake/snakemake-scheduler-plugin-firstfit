### How this Plugin works

In this plugin, jobs are selected for run in a [first-fit with one bin](https://en.wikipedia.org/wiki/First-fit_bin_packing) way.

Briefly, available jobs are sequentially evaluated (in whatever order they appear) and selected for submission if there are available resources. Alternatively, if `--scheduler-plugin-greediness` is provided, jobs are previously sorted by their `reward` so that higher-reward jobs are evaluated first.

### Contributions

We welcome bug reports, feature requests, and pull requests!
Please report issues specific to this plugin [in the plugin's GitHub repository](https://github.com/snakemake/snakemake-scheduler-plugin-firstfit/issues).

### Configuration

Snakemake offers great [capabilities to specify and thereby limit resources](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#resources) used by a workflow as a whole and by individual jobs.
