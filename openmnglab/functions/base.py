from abc import ABC
from typing import Optional, Iterable

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunction, IFunctionDefinition


class DefaultFunctionBase(IFunction, ABC):

    def validate_input(self) -> bool:
        return True


class SourceFunctionBase(DefaultFunctionBase, ABC):

    def set_input(self):
        """Does nothing as source functions don't accept any input"""
        pass


class FunctionDefinitionBase(IFunctionDefinition, ABC):

    def __init__(self, identifier: str):
        self._identifier = identifier

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def config_hash(self) -> bytes:
        return bytes()

    @property
    def consumes(self) -> Optional[Iterable[IDataScheme]]:
        return

    @property
    def produces(self) -> Optional[Iterable[IDataScheme]]:
        return
