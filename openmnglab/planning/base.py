from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Collection, TypeVar, Generic, Optional, Iterable

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.exceptions import InvalidFunctionArgumentCountError, FunctionArgumentSchemaError, PlanningError
from openmnglab.planning.interface import IExecutionPlanner, IProxyData
from openmnglab.planning.plan.interface import IExecutionPlan, IPlannedFunction, IPlannedData


def check_input(expected_schemes: Collection[IDataScheme], actual_schemes: Collection[IDataScheme]):
    if len(expected_schemes) != len(actual_schemes):
        raise InvalidFunctionArgumentCountError(len(expected_schemes), len(actual_schemes))
    for pos, (expected_scheme, actual_scheme) in enumerate(zip(expected_schemes, actual_schemes)):
        try:
            if not expected_scheme.is_compatible(actual_scheme):
                raise DataSchemeCompatibilityError("Expected scheme is not compatible with actual scheme")
        except DataSchemeCompatibilityError as ds_compat_err:
            raise FunctionArgumentSchemaError(pos) from ds_compat_err


@dataclass
class ExecutionPlan(IExecutionPlan):
    functions: dict[bytes, IPlannedFunction]
    proxy_data: dict[bytes, IProxyData]


_FuncT = TypeVar('_FuncT', bound=IPlannedFunction)
_DataT = TypeVar('_DataT', bound=IPlannedData)


class PlannerBase(IExecutionPlanner, ABC, Generic[_FuncT, _DataT]):

    def __init__(self):
        self._functions: dict[bytes, _FuncT] = dict()
        self._proxy_data: dict[bytes, _DataT] = dict()

    def get_plan(self) -> ExecutionPlan:
        return ExecutionPlan(self._functions.copy(), self._proxy_data.copy())

    @abstractmethod
    def _add_function(self, function: IFunctionDefinition, *inp_data: _DataT) -> Optional[tuple[IProxyData]]:
        ...

    def add_function(self, function: IFunctionDefinition, *inp_data: IProxyData) -> Optional[tuple[IProxyData]]:
        return self._add_function(function, *self._proxy_data_to_concrete(*inp_data))

    def _proxy_data_to_concrete(self, *inp_data: IProxyData) -> Iterable[_DataT]:
        for pos, inp in enumerate(inp_data):
            concrete_data = self._proxy_data.get(inp.calculated_hash)
            if concrete_data is None:
                raise PlanningError(
                    f"Argument at position {pos} with hash {inp.calculated_hash.hex()} is not part of this plan and therefore cannot be used as an argument in it")
            yield concrete_data
