from abc import ABC, abstractmethod
from typing import Mapping, Optional

from openmnglab.model.datamodel.interface import IDataContainer
from openmnglab.model.planning.interface import DCT, IProxyData


class IExecutor(ABC):
    @abstractmethod
    def execute(self):
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