from abc import ABC
from typing import Generic

from openmnglab.functions.interface import IFunction, IFunctionDefinition, ISourceFunction, Prods, \
    IStaticFunctionDefinition, ISourceFunctionDefinition
from openmnglab.util.hashing import Hash

PandasSelector = str | int

class FunctionBase(IFunction, ABC):

    def validate_input(self) -> bool:
        return True


class SourceFunctionBase(FunctionBase, ISourceFunction, ABC):

    def set_input(self):
        """Does nothing as source functions don't accept any input"""
        pass


class FunctionDefinitionBase(Generic[*Prods], IFunctionDefinition[*Prods], ABC):

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


class StaticFunctionDefinitionBase(Generic[*Prods], FunctionDefinitionBase[*Prods], IStaticFunctionDefinition[*Prods],
                                   ABC):
    ...


class SourceFunctionDefinitionBase(Generic[*Prods], StaticFunctionDefinitionBase[*Prods],
                                   ISourceFunctionDefinition[*Prods], ABC):
    ...
