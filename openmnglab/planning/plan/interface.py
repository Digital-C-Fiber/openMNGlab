from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Iterable, Collection

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.interface import IProxyData, IPlannedElement


class IPlannedData(IPlannedElement, ABC):
    @property
    @abstractmethod
    def schema(self) -> IDataScheme:
        ...

    @property
    @abstractmethod
    def produced_by(self) -> IPlannedFunction:
        ...


class IPlannedFunction(IPlannedElement, ABC):
    @property
    @abstractmethod
    def definition(self) -> IFunctionDefinition:
        ...

    @property
    @abstractmethod
    def input(self) -> Collection[IPlannedData]:
        ...

    @property
    @abstractmethod
    def output(self) -> Collection[IPlannedData]:
        ...


class IExecutionPlan(ABC):

    @property
    @abstractmethod
    def functions(self) -> Mapping[bytes, IPlannedFunction]:
        ...

    @property
    @abstractmethod
    def proxy_data(self) -> Mapping[bytes, IPlannedData]:
        ...
