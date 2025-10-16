from typing import Optional, Type
from snakemake_interface_scheduler_plugins.base import SchedulerBase
from snakemake_interface_scheduler_plugins.settings import SchedulerSettingsBase
from snakemake_interface_scheduler_plugins.tests import TestSchedulerBase

from snakemake_scheduler_plugin_firstfit import Scheduler, SchedulerSettings


class FirstFitScheduler(TestSchedulerBase):
    # This ensures that the tests from the base class are executed.
    # Set to False if you want to implement intermediate base classes.
    __test__ = True

    def get_scheduler_cls(self) -> Type[SchedulerBase]:
        # Return the scheduler class of your plugin.
        return Scheduler

    def get_scheduler_settings(self) -> Optional[SchedulerSettingsBase]:
        # Return the SchedulerSettings instance you want to test.
        # Note that you can put here multiple classes inheriting from TestSchedulerBase
        # or from each other to test different settings.
        return SchedulerSettings(
            greediness=0.5,
            omit_prioritize_by_temp_and_input=True,
        )
