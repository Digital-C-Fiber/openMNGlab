from abc import ABC, abstractmethod
from typing import Optional, Iterable, Sequence, Literal, Generic, TypeVar

from openmnglab.model.datamodel.interface import IDataContainer, IInputDataScheme, IOutputDataScheme


class IFunction(ABC):
    """A concrete instance of a function to compute something.
    Function to operate on must be set using :meth:`set_input` before executing the function with :meth:`execute`.

    Implementation details
    ======================
    * :meth:`set_input` **should not validate the data**, but only store it internally so subsequent calls to :meth:`execute` or :meth:`validate_input` can access it.
    * Implementations should assume that they have an *exclusive copy of the data* to work on and should not copy input data defensively
    * Implementations may perform additional validations for the data in :meth:`validate_input` for debugging purposes, but there is no guarantee that the method is called by the integration layer.
    """

    @abstractmethod
    def execute(self) -> Optional[IDataContainer | Iterable[IDataContainer]]:
        """ Execute the function based on the data set by :meth:`set_input`

        :return: The data containers produced by executing the function
        """
        ...

    @abstractmethod
    def set_input(self, *data_in: IDataContainer):
        """ Sets the input data for this function

        :param data_in: The input data
        """
        ...

    @abstractmethod
    def validate_input(self) -> bool:
        ...


class ISourceFunction(IFunction, ABC):

    @abstractmethod
    def set_input(self):
        ...


ProxyRet = TypeVar('ProxyRet')


class IFunctionDefinition(ABC, Generic[ProxyRet]):

    @property
    @abstractmethod
    def identifier(self) -> str:
        ...

    @property
    @abstractmethod
    def config_hash(self) -> bytes:
        ...

    @property
    @abstractmethod
    def identifying_hash(self) -> bytes:
        ...

    @property
    @abstractmethod
    def consumes(self) -> Optional[Sequence[IInputDataScheme] | IInputDataScheme]:
        ...

    @abstractmethod
    def production_for(self, *inputs: IOutputDataScheme) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
        ...

    @abstractmethod
    def new_function(self) -> IFunction:
        ...


class IStaticFunctionDefinition(Generic[ProxyRet], IFunctionDefinition[ProxyRet], ABC):
    @property
    @abstractmethod
    def produces(self) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
        ...

    def production_for(self, *_: IOutputDataScheme) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
        return self.produces


class ISourceFunctionDefinition(Generic[ProxyRet], IStaticFunctionDefinition[ProxyRet], ABC):

    @property
    def consumes(self) -> None:
        return None

    def production_for(self) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
        return self.produces

    @abstractmethod
    def new_function(self) -> ISourceFunction:
        ...
