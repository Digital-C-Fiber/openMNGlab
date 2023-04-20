from abc import abstractmethod, ABC
from typing import Iterable, TypeVar, Generic, Mapping, Optional

from openmnglab.datamodel.interface import IDataScheme, IDataContainer
from openmnglab.functions.interface import IFunctionDefinition


class IPlannedFunction(ABC):
    @property
    @abstractmethod
    def definition(self) -> IFunctionDefinition:
        ...

    @property
    @abstractmethod
    def calculated_hash(self) -> bytes:
        ...

    @property
    @abstractmethod
    def depth(self) -> int:
        ...

    @property
    @abstractmethod
    def input(self) -> Iterable:
        ...

    @property
    @abstractmethod
    def output(self) -> Iterable:
        ...


DCT = TypeVar('DCT', bound=IDataContainer)


class IProxyData(ABC, Generic[DCT]):

    @property
    @abstractmethod
    def schema(self) -> IDataScheme:
        ...

    @property
    @abstractmethod
    def produced_by(self) -> IPlannedFunction:
        ...

    @property
    @abstractmethod
    def calculated_hash(self) -> bytes:
        ...


class IExecutionPlan(ABC):

    @property
    @abstractmethod
    def functions(self) -> Mapping[bytes, IPlannedFunction]:
        ...

    @property
    @abstractmethod
    def proxy_data(self) -> Mapping[bytes, IProxyData]:
        ...

class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition, *input: IProxyData) -> Optional[tuple[IDataScheme]]:
        ...

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...
