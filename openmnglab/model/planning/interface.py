from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TypeVar, Generic

from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.functions.interface import IFunctionDefinition, ISourceFunctionDefinition, ProxyRet
from openmnglab.model.planning.plan.interface import IExecutionPlan


class IExecutionPlanner(ABC):

    @abstractmethod
    def add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: IDataReference) -> ProxyRet:
        ...

    def add_source(self, function: ISourceFunctionDefinition[ProxyRet]) -> ProxyRet:
        return self.add_function(function)

    def add_stage(self, function: IFunctionDefinition[ProxyRet], input_0: IDataReference,
                  *other_inputs: IDataReference) -> ProxyRet:
        return self.add_function(function, input_0, *other_inputs)

    @abstractmethod
    def get_plan(self) -> IExecutionPlan:
        ...


DCT = TypeVar('DCT', bound=IDataContainer)


class IDataReference(Generic[DCT], ABC):

    @property
    @abstractmethod
    def referenced_data_id(self) -> bytes:
        ...
