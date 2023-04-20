from abc import ABC
from dataclasses import dataclass
from typing import Optional

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition

from openmnglab.planning.interface import IExecutionPlan, IExecutionPlanner, IPlannedFunction, IProxyData


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


