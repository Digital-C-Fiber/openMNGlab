from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T_co = TypeVar('T_co', covariant=True)


class IDataContainer(ABC, Generic[T_co]):

    @abstractmethod
    @property
    def data(self) -> T_co:
        ...


class IDataScheme(ABC):

    @abstractmethod
    def is_compatible(self, other: IDataScheme) -> bool:
        ...

    @abstractmethod
    def verify(self, data: object) -> bool:
        ...
