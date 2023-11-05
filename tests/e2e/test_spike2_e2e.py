import pathlib

import pytest

from openmnglab.execution import SingleThreadedExecutor
from openmnglab.functions.input.readers.spike2_reader import Spike2Reader
from openmnglab.planning import DefaultPlanner

#SPIKE2_TEST_FILE_PATHS: list[pathlib.Path] = [file for file in SPIKE2_TESTDATA_ROOT.rglob(SPIKE2_TESTDATA_GLOB)]

class TestSpike2E2E:

    @pytest.fixture(scope='class')
    def planner(self) -> DefaultPlanner:
        return DefaultPlanner()

    @pytest.fixture(scope='class')
    def executor(self):
        return SingleThreadedExecutor()

    @pytest.fixture(scope='class')
    def file_spike2(self, request):
        return request.data
    @pytest.fixture(scope='class')
    def spike2_data(self, file_spike2, planner):
        return planner.add_source(Spike2Reader(file_spike2))

    @pytest.fixture(scope='class')
    def signal(self, spike2_data):
        return spike2_data[0]

    def test_execute(self, executor, planner, spike2_data):
        executor.execute(planner.get_plan())

