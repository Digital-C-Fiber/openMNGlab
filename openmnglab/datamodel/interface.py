from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T_co = TypeVar('T_co', covariant=True)


class IDataContainer(ABC, Generic[T_co]):
    """
    A structures carrying data between processing stages
    """

    @property
    @abstractmethod
    def data(self) -> T_co:
        """
        :return: Primary datastructure stored in this container
        """
        ...


class IDataScheme(ABC):
    """
    Validates connections between stages and verifies that stage outputs conform to their
    advertised scheme
    """

    @abstractmethod
    def is_compatible(self, other: IDataScheme) -> bool:
        """
        Checks if this data scheme is compatible with the other data scheme.
        If botch schemes are compatible, the implementation returns ``True``.
        If they are not compatible, the implementation either raises an exception containing details or returns ``False``.

        :param other: The other datas cheme to check the compatibility against
        :raise DataSchemeCompatibilityError: If the schemes are not compatible to each other and detailed information is available
        :return: ``True`` if the data schemes are compatible
        """
        ...

    @abstractmethod
    def verify(self, data: object) -> bool:
        """
        Verifies that a data object conforms to the schema defined by this instance.
        May raise an exception containing more information why the data does not conform to this scheme

        :param data: The object to check
        :raise DataSchemeConformityError: If data does not conform to the scheme and detailed information is available
        :return: True if the data object conforms to this schema
        """
        ...
