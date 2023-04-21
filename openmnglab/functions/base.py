from abc import ABC
from typing import Optional, Iterable, Sequence

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunction, IFunctionDefinition, ISourceFunction
from openmnglab.util.hashing import Hash


class DefaultFunctionBase(IFunction, ABC):

    def validate_input(self) -> bool:
        return True


class SourceFunctionBase(DefaultFunctionBase, ISourceFunction, ABC):

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
    def identifying_hash(self) -> bytes:
        hashgen = Hash()
        hashgen.str(self.identifier)
        hashgen.update(self.config_hash)
        return hashgen.digest()

    @property
    def consumes(self) -> Optional[Sequence[IDataScheme]]:
        return None

    @property
    def produces(self) -> Optional[Sequence[IDataScheme]]:
        return None
