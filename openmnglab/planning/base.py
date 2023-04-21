from abc import ABC
from dataclasses import dataclass
from typing import Collection

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.exceptions import InvalidFunctionArgumentCountError, FunctionArgumentSchemaError, PlanningError
from openmnglab.planning.interface import IExecutionPlanner, IProxyData
from openmnglab.planning.plan.interface import IExecutionPlan, IPlannedFunction


@dataclass
class ExecutionPlan(IExecutionPlan):
    functions: dict[bytes, IPlannedFunction]
    proxy_data: dict[bytes, IProxyData]


class PlannerBase(IExecutionPlanner, IExecutionPlan, ABC):

    def __init__(self):
        self._functions: dict[bytes, IPlannedFunction] = dict()
        self._proxy_data: dict[bytes, IProxyData] = dict()

    @property
    def functions(self) -> dict[bytes, IPlannedFunction]:
        return self._functions

    @property
    def proxy_data(self) -> dict[bytes, IProxyData]:
        return self._proxy_data

    def get_plan(self) -> ExecutionPlan:
        return ExecutionPlan(self.functions.copy(), self.proxy_data.copy())

    def verify_args(self, function: IFunctionDefinition, *input: IProxyData):
        for pos, inp in enumerate(input):
            if inp.calculated_hash not in self.proxy_data:
                raise PlanningError(
                    f"Argument at position {pos} with hash {inp.calculated_hash.hex()} is not part of this plan and therefore cannot be used as an argument in it")
        self._check_input(tuple(function.consumes), tuple(inp.schema for inp in input))

    @staticmethod
    def _check_input(expected_schemes: Collection[IDataScheme], actual_schemes: Collection[IDataScheme]):
        if len(expected_schemes) != len(actual_schemes):
            raise InvalidFunctionArgumentCountError(len(expected_schemes), len(actual_schemes))
        for pos, (expected_scheme, actual_scheme) in enumerate(zip(expected_schemes, actual_schemes)):
            try:
                if not expected_scheme.is_compatible(actual_scheme):
                    raise DataSchemeCompatibilityError("Expected scheme is not compatible with actual scheme")
            except DataSchemeCompatibilityError as ds_compat_err:
                raise FunctionArgumentSchemaError(pos) from ds_compat_err
