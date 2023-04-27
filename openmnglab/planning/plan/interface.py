from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Sequence, TypeVar, Generic

from openmnglab.datamodel.interface import IDataScheme, IDataContainer
from openmnglab.functions.interface import IFunctionDefinition


class IHashIdentifiedElement(ABC):
    @property
    @abstractmethod
    def calculated_hash(self) -> bytes:
        ...


class IPlannedElement(IHashIdentifiedElement, ABC):
    @property
    @abstractmethod
    def depth(self) -> int:
        ...


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


DCT = TypeVar('DCT', bound=IDataContainer)


class IProxyData(IHashIdentifiedElement, ABC, Generic[DCT]):
    ...
