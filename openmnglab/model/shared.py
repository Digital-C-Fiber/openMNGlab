from __future__ import annotations

from abc import ABC, abstractmethod


class IHashIdentifiedElement(ABC):
    @property
    @abstractmethod
    def planning_id(self) -> bytes:
        ...
