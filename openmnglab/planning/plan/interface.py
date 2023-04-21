from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Iterable, Collection, Sequence

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
    def data_in(self) -> Sequence[IPlannedData]:
        ...

    @property
    @abstractmethod
    def data_out(self) -> Sequence[IPlannedData]:
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
