from abc import ABC, abstractmethod
from typing import Mapping, Iterable

from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.interface import IProxyData, IPlannedElement


class IExecutionPlan(ABC):

    @property
    @abstractmethod
    def functions(self) -> Mapping[bytes, IPlannedFunction]:
        ...

    @property
    @abstractmethod
    def proxy_data(self) -> Mapping[bytes, IProxyData]:
        ...


class IPlannedFunction(IPlannedElement, ABC):
    @property
    @abstractmethod
    def definition(self) -> IFunctionDefinition:
        ...

    @property
    @abstractmethod
    def input(self) -> Iterable:
        ...

    @property
    @abstractmethod
    def output(self) -> Iterable:
        ...
