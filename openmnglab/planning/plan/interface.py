from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Sequence

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.shared import IHashIdentifiedElement


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
    def planned_data(self) -> Mapping[bytes, IPlannedData]:
        ...


