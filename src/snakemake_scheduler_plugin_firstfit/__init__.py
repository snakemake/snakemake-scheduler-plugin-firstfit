from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Sequence, Union

from snakemake_interface_scheduler_plugins.settings import SchedulerSettingsBase
from snakemake_interface_scheduler_plugins.base import SchedulerBase
from snakemake_interface_scheduler_plugins.interfaces.jobs import JobSchedulerInterface
from snakemake_interface_common.io import AnnotatedStringInterface


# Optional:
# Define settings for your scheduler plugin.
# They will occur in the Snakemake CLI as --scheduler-<plugin-name>-<param-name>
# Make sure that all defined fields are 'Optional' and specify a default value
# of None or anything else that makes sense in your case.
@dataclass
class SchedulerSettings(SchedulerSettingsBase):
    greediness: Optional[float] = field(
        default=0,
        metadata={
            "help": "Set the greediness (i.e. size) of the heap queue. This will "
            "enable the heap-queue pre-evaluation step, where available jobs are "
            "sorted based on their rewards. This value (between 0 and 1) determines "
            "how many jobs will be evaluated for execution. A greediness of 1 will "
            "only evaluate `--max-jobs-per-timespan` jobs, while a value of 0 will "
            "evaluate all available jobs."
        },
    )
    omit_prioritize_by_temp_and_input: bool = field(
        default=False,
        metadata={
            "help": "If set, the size of temporary or input files is not taken into "
            "account when prioritizing. By default, it is  assumed that temp files "
            "should be removed as soon as possible, and larger input files may take "
            "longer to process, so it is better to start them earlier.",
        },
    )

    def __post_init__(self):
        if not (0 <= self.greediness <= 1.0):
            raise ValueError("greediness must be >=0 and <=1.")


# Inside of the Scheduler, you can use self.logger (a normal Python logger of type
# logging.Logger) to log any additional informations or warnings.
class Scheduler(SchedulerBase):
    def select_jobs(
        self,
        selectable_jobs: Sequence[JobSchedulerInterface],
        remaining_jobs: Sequence[JobSchedulerInterface],
        available_resources: Mapping[str, Union[int, str]],
        input_sizes: Mapping[AnnotatedStringInterface, int],
    ) -> Optional[Sequence[JobSchedulerInterface]]:
        # Select jobs from the selectable jobs sequence. Thereby, ensure that the selected
        # jobs do not exceed the available resources.

        # Job resources are available via Job.scheduler_resources.

        # Jobs are either single (SingleJobSchedulerInterface) or group jobs (GroupJobSchedulerInterface).
        # Single jobs inside a group job can be obtained with GroupJobSchedulerInterface.jobs().

        # While selecting, jobs can be given additional resources that are not
        # yet defined in the job itself via Job.add_resource(name: str, value: int | str).

        # The argument remaining_jobs contains all jobs that still have to be executed
        # at some point, including the currently selectable jobs.

        # input_sizes provides a mapping of given input files to their sizes.
        # This can e.g. be used to prioritize jobs with larger input files or to weight
        # the footprint of temporary files. The function uses async I/O under the hood,
        # thus make sure to call it only once per job selection and collect all files of
        # interest for a that single call.

        # Return None to indicate an error in the selection process that shall lead to
        # a fallback to the Snakemake's internal greedy scheduler.
        # Otherwise, return the sequence of selected jobs.

        import random
        import heapq
        from collections import defaultdict

        self.logger.debug("Selecting jobs to run using first-fit scheduler.")

        # Linear interpolation between selecting from all jobs (greediness == 0)
        # to just those specified by `--max-jobs-per-timespan` (greediness == 1)
        # Get max_jobs from rate limiter, with fallback for test environments
        try:
            max_jobs = self.dag.workflow.scheduler.job_rate_limiter.max_jobs
        except AttributeError:
            # Fallback for test environments or when workflow/scheduler not available
            max_jobs = 1000
        n = int(
            (1 - self.settings.greediness) * len(selectable_jobs)
            + self.settings.greediness * max_jobs
        )
        self.logger.debug(
            f"Using greediness of {self.settings.greediness} for job selection (at most {n} jobs)."
        )

        # Populate heap
        jobs_heap = []
        for job in selectable_jobs:
            # Get job rewards
            job_rewards = self.job_reward(job, input_sizes)
            # Store the reward as the first element of a tuple (used for sorting), a random
            # number as second element (to break-up ties), and job name as third element (to keep track).
            if len(jobs_heap) <= n:
                # If the heap is not full (or not limited), push the current reward.
                heapq.heappush(jobs_heap, (job_rewards, random.random(), job))
            else:
                # If the heap is full, replace the smallest element if the new reward is better.
                heapq.heappushpop(jobs_heap, (job_rewards, random.random(), job))
        # Revert heap
        _selectable_jobs = [heapq.heappop(jobs_heap)[2] for i in range(len(jobs_heap))]
        self.logger.debug(f"Jobs heap: {_selectable_jobs}")

        # Iterate jobs, picking the last element at a time, until all elements
        # have been picked, or resources exhausted
        solution = []
        used_resources = defaultdict(int)
        while _selectable_jobs:
            # Get next job
            job = _selectable_jobs.pop()
            job_resources = self.job_resources(job, available_resources)

            # Check if adding job would exhaust some resources
            exhausted_resources = {
                res: used_resources[res] + job_resources[res] > val
                for res, val in available_resources.items()
            }

            # If resource limits not yet exceeded
            if not any(exhausted_resources.values()):
                # Update used resources
                for res, val in job_resources.items():
                    used_resources[res] += val
                # Add job
                solution.append(job)

        return solution

    def job_resources(self, job, available_resources: Mapping[str, Union[int, str]]):
        res = job.scheduler_resources
        return {name: res.get(name, 0) for name in available_resources}

    def job_reward(self, job, input_sizes: Dict[AnnotatedStringInterface, int]):
        if self.settings.omit_prioritize_by_temp_and_input:
            return job.priority
        else:
            return (
                job.priority,
                sum(input_sizes[f] or 0 for f in job.input if f.is_flagged("temp")),
                sum(input_sizes[f] or 0 for f in job.input),
            )
