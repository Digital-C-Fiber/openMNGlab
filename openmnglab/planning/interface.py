from abc import abstractmethod, ABC
from typing import TypeVar, Generic, Optional

from openmnglab.datamodel.interface import IDataScheme, IDataContainer
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.plan.interface import IExecutionPlan, IPlannedFunction

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

    @property
    @abstractmethod
    def schema(self) -> IDataScheme:
        ...

    @property
    @abstractmethod
    def produced_by(self) -> IPlannedFunction:
        ...


class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition, *input: IProxyData) -> Optional[tuple[IProxyData]]:
        ...

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...
