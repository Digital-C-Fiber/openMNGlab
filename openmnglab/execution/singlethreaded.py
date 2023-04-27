from typing import Mapping, Optional, Iterable

from openmnglab.datamodel.interface import IDataContainer
from openmnglab.execution.exceptions import FunctionInputError, FunctionExecutionError, FunctionReturnCountMissmatch
from openmnglab.execution.interface import IExecutor
from openmnglab.functions.interface import IFunction
from openmnglab.planning.plan.interface import IExecutionPlan, IPlannedData
from openmnglab.planning.interface import IProxyData


def _func_setinput(func: IFunction, *inp: IDataContainer):
    try:
        return func.set_input(*inp)
    except Exception as e:
        raise FunctionInputError("failed to set input of function") from e


def _func_exec(func: IFunction) -> Iterable[IDataContainer]:
    try:
        ret = func.execute()
        return ret if ret is not None else tuple()
    except Exception as e:
        raise FunctionExecutionError("function failed to execute") from e


class SingleThreadedExecutor(IExecutor):
    def __init__(self, plan: IExecutionPlan):
        self._plan = plan
        self._data: dict[bytes, IDataContainer] = dict()

    @property
    def data(self) -> Mapping[bytes, IDataContainer]:
        return self._data

    def has_computed(self, proxy_data: IProxyData) -> bool:
        return proxy_data.calculated_hash in self._data

    def execute(self):
        for planned_func in sorted(self._plan.stages.values(), key=lambda x: x.depth):
            input_values = tuple(self._data[dependency.calculated_hash] for dependency in planned_func.data_in)
            func = planned_func.definition.new_function()
            _func_setinput(func, *input_values)
            results: tuple[IDataContainer] = tuple(_func_exec(func))
            if len(results) != len(planned_func.data_out):
                raise FunctionReturnCountMissmatch(expected=len(planned_func.data_out), actual=len(results))
            for planned_data_output, actual_data_output in zip(planned_func.data_out, results):
                actual_data_output: IDataContainer
                planned_data_output: IPlannedData
                planned_data_output.schema.verify(actual_data_output.data)
                self._data[planned_data_output.calculated_hash] = actual_data_output
