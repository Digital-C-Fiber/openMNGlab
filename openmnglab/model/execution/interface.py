from abc import ABC, abstractmethod
from typing import Mapping, Optional

from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.planning.interface import DCT, IDataReference
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
    def has_computed(self, proxy_data: IDataReference) -> bool:
        ...

    def get(self, proxy_data: IDataReference[DCT]) -> Optional[DCT]:
        return self.data.get(proxy_data.referenced_data_id) if self.has_computed(proxy_data) else None
