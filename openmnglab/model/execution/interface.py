from abc import ABC, abstractmethod
from typing import Mapping, Optional

from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.planning.interface import DCT, IProxyData
from openmnglab.model.planning.plan.interface import IExecutionPlan


class IExecutor(ABC):
    @abstractmethod
    def execute(self, plan: IExecutionPlan, ignore_previous=False):
        ...

    @property
    @abstractmethod
    def data(self) -> Mapping[bytes, IDataContainer]:
        ...

    @abstractmethod
    def has_computed(self, proxy_data: IProxyData) -> bool:
        ...

    def get(self, proxy_data: IProxyData[DCT]) -> Optional[DCT]:
        return self.data.get(proxy_data.calculated_hash) if self.has_computed(proxy_data) else None
