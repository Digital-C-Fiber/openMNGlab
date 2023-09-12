from abc import ABC
from typing import Generic

from openmnglab.model.functions.interface import IFunction, IFunctionDefinition, ISourceFunction, ProxyRet, \
    IStaticFunctionDefinition, ISourceFunctionDefinition

PandasSelector = str | int


class FunctionBase(IFunction, ABC):
    ...


class SourceFunctionBase(FunctionBase, ISourceFunction, ABC):

    def set_input(self):
        """Does nothing as source functions don't accept any input"""
        pass


class FunctionDefinitionBase(Generic[ProxyRet], IFunctionDefinition[ProxyRet], ABC):

    def __init__(self, identifier: str):
        self._identifier = identifier

    @property
    def identifier(self) -> str:
        return self._identifier


class StaticFunctionDefinitionBase(Generic[ProxyRet], FunctionDefinitionBase[ProxyRet],
                                   IStaticFunctionDefinition[ProxyRet],
                                   ABC):
    ...


class SourceFunctionDefinitionBase(Generic[ProxyRet], StaticFunctionDefinitionBase[ProxyRet],
                                   ISourceFunctionDefinition[ProxyRet], ABC):
    ...
