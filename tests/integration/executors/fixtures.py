import pytest

from tests.integration.spy import SpyObserver


class ObserverFixture:
    @pytest.fixture
    def obs(self):
        return SpyObserver()
