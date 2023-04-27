from abc import abstractmethod, ABC
from typing import Optional

from openmnglab.functions.interface import IFunctionDefinition, ISourceFunctionDefinition, Prods
from openmnglab.planning.plan.interface import IExecutionPlan, IProxyData


class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition[*Prods], *inp_data: IProxyData) -> Optional[tuple[*Prods]]:
        ...

    def add_source(self, function: ISourceFunctionDefinition[*Prods]) -> tuple[*Prods]:
        return self.add_function(function)

    def add_stage(self, function: IFunctionDefinition[*Prods], input_0: IProxyData, *other_inputs: IProxyData) -> tuple[
        *Prods]:
        return self.add_function(function, input_0, *other_inputs)

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...
