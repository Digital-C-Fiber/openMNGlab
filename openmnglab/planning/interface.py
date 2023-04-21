from abc import abstractmethod, ABC
from typing import TypeVar, Generic, Optional

from openmnglab.datamodel.interface import IDataContainer
from openmnglab.functions.interface import IFunctionDefinition, ISourceFunctionDefinition
from openmnglab.planning.plan.interface import IExecutionPlan

DCT = TypeVar('DCT', bound=IDataContainer)


class IPlannedElement(ABC):
    @property
    @abstractmethod
    def calculated_hash(self) -> bytes:
        ...

    @property
    @abstractmethod
    def depth(self) -> int:
        ...


class IProxyData(IPlannedElement, ABC, Generic[DCT]):
    ...


class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition, *inp_data: IProxyData) -> Optional[tuple[IProxyData, ...]]:
        ...

    def add_source(self, function: ISourceFunctionDefinition) -> tuple[IProxyData, ...]:
        return self.add_function(function)

    def add_stage(self, function: IFunctionDefinition, input_0: IProxyData, *other_inputs: IProxyData) -> tuple[
        IProxyData, ...]:
        return self.add_function(function, input_0, *other_inputs)

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...
