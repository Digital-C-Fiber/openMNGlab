from abc import ABC, abstractmethod
from typing import Mapping, Optional

from openmnglab.datamodel.interface import IDataContainer
from openmnglab.planning.interface import IProxyData, DCT


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
