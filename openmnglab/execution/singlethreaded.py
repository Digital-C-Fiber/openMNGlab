from typing import Mapping, Iterable

from openmnglab.execution.exceptions import FunctionInputError, FunctionExecutionError, FunctionReturnCountMissmatch
from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.execution.interface import IExecutor
from openmnglab.model.functions.interface import IFunction
from openmnglab.model.planning.interface import IDataReference
from openmnglab.model.planning.plan.interface import IExecutionPlan, IVirtualData, IStage
from openmnglab.util.iterables import ensure_iterable


class SingleThreadedExecutor(IExecutor):
    def __init__(self):
        self._data: dict[bytes, IDataContainer] = dict()

    @property
    def data(self) -> Mapping[bytes, IDataContainer]:
        return self._data

    def has_computed(self, proxy_data: IDataReference) -> bool:
        return proxy_data.referenced_data_id in self._data

    @staticmethod
    def _set_func_input(func: IFunction, *inp: IDataContainer):
        """Sets the input of the function and throws a descriptive exception when it fails"""
        try:
            return func.set_input(*inp)
        except Exception as e:
            raise FunctionInputError("failed to set input of function") from e

    @staticmethod
    def _exec_func(func: IFunction) -> Iterable[IDataContainer]:
        """Executes the function and ensures that return is iterable.
        Also throws a descriptive exception when it fails
        """
        try:
            return ensure_iterable(func.execute(), IDataContainer)
        except Exception as e:
            raise FunctionExecutionError("function failed to execute") from e

    def compute_stage(self, stage: IStage):
        """Runs the function a stage and stores it output.

        .. warn:: Caller must ensure that required input data of the stage is present in :attr:`~.data`
        """
        try:
            input_values = tuple(self._data[dependency.planning_id] for dependency in stage.data_in)
            func = stage.definition.new_function()
            self._set_func_input(func, *input_values)
            results: tuple[IDataContainer] = tuple(self._exec_func(func))
            if len(results) != len(stage.data_out):
                raise FunctionReturnCountMissmatch(expected=len(stage.data_out), actual=len(results))
            for i, (planned_data_output, actual_data_output) in enumerate(zip(stage.data_out, results)):
                actual_data_output: IDataContainer
                planned_data_output: IVirtualData
                try:
                    planned_data_output.schema.validate(actual_data_output)
                except Exception as e:
                    raise Exception(f"Schema validation of output #{i} failed") from e
                self._data[planned_data_output.planning_id] = actual_data_output
        except Exception as e:
            raise FunctionExecutionError(
                f"Failed to execute {stage.definition.identifier} (stage {stage.planning_id.hex()})")

    def execute(self, plan: IExecutionPlan, ignore_previous=False):
        for stage in sorted(plan.stages.values(), key=lambda x: x.depth):
            if ignore_previous or not all(
                    planned_output.planning_id in self._data for planned_output in stage.data_out):
                self.compute_stage(stage)
