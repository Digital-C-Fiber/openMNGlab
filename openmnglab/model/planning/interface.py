from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Optional, TypeVar, Generic

from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.functions.interface import IFunctionDefinition, ISourceFunctionDefinition, ProxyRet
from openmnglab.model.planning.plan.interface import IExecutionPlan
from openmnglab.model.shared import IHashIdentifiedElement


class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: IProxyData) -> ProxyRet:
        ...

    def add_source(self, function: ISourceFunctionDefinition[ProxyRet]) -> ProxyRet:
        return self.add_function(function)

    def add_stage(self, function: IFunctionDefinition[ProxyRet], input_0: IProxyData, *other_inputs: IProxyData) -> ProxyRet:
        return self.add_function(function, input_0, *other_inputs)

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...


DCT = TypeVar('DCT', bound=IDataContainer)


class IProxyData(IHashIdentifiedElement, ABC, Generic[DCT]):
    ...
