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

    @abstractmethod
    def deep_copy(self) -> IDataContainer[T_co]:
        ...


class ISchemaAcceptor(ABC):
    """
    Scheme for data that is expected as input for a function
    """

    @abstractmethod
    def accepts(self, output_data_scheme: IDataSchema) -> bool:
        """Assess whether this scheme would accept the other data scheme as input.

        If the schemes are incompatible, the function may either raise an exception containing further details on why the
        other data scheme is not accepted as input or just return ``False``

        :raise DataSchemeCompatibilityError: If the data schemes are not compatible and further details are available
        :param output_data_scheme: Output data scheme to check for compatibility
        :return: ``True`` if the output data scheme is accepted as input, ``False`` otherwise
        """
        ...


class IDataSchema(ISchemaAcceptor, ABC):
    """
    Scheme for data that is produced by a function.
    """

    @abstractmethod
    def validate(self, data_container: IDataContainer) -> bool:
        """Validates that a data container fits this scheme.

        If this is not the case, the function may either raise an exception containing further details on why the validation
        failed or just return ``False``
        :raise DataSchemeConformityError: If the schemes are not compatible to each other and detailed information is available
        :param data_container: Data container to validate
        :return: ``True`` if the data container conforms to this scheme, ``False`` otherwise.
        """
        ...
