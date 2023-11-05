import glob
import pathlib

import pytest
import pytest_cases
import quantities as pq


from openmnglab.execution import SingleThreadedExecutor
from openmnglab.functions import DapsysReader, StaticIntervals, Windows, SPDFComponents, SPDFFeatures, WaveformPlot, \
    WaveformPlotMode
from openmnglab.planning import DefaultPlanner
import openmnglab.datamodel.pandas.schemas as schema


class TestDapsysE2E:
    @pytest.fixture(scope='class')
    def planner(self) -> DefaultPlanner:
        return DefaultPlanner()

    @pytest.fixture(scope='class')
    def executor(self):
        return SingleThreadedExecutor()

    @pytest.fixture(scope='class')
    def dapsys_file(self, file_dapsys):
        return file_dapsys

    @pytest.fixture(scope='class')
    def dapsys_data(self, dapsys_file, planner):
        return planner.add_source(DapsysReader(dapsys_file))

    @pytest.fixture(scope='class')
    def signal(self, dapsys_data):
        return dapsys_data[0]

    @pytest.fixture(scope='class')
    def stims(self, dapsys_data):
        return dapsys_data[1]

    @pytest.fixture(scope='class')
    def tracks(self, dapsys_data):
        return dapsys_data[2]

    @pytest.fixture(scope='class')
    def comments(self, dapsys_data):
        return dapsys_data[3]

    @pytest.fixture(scope='class')
    def stimdefs(self, dapsys_data):
        return dapsys_data[4]

    @pytest.fixture(scope='class')
    def static_intervals(self, planner, tracks):
        return planner.add_stage(StaticIntervals(-2 * pq.ms, 3 * pq.ms, "spike_windows"), tracks)

    @pytest.fixture(scope='class')
    def windows(self, planner, static_intervals, signal):
        return planner.add_stage(Windows(0, 1, 2, derivative_base=pq.ms), static_intervals, signal)

    @pytest.fixture(scope='class')
    def spdf_components(self, planner, windows):
        return planner.add_stage(SPDFComponents(), windows)

    @pytest.fixture(scope='class')
    def spdf_features(self, planner, spdf_components, windows):
        return planner.add_stage(SPDFFeatures(), spdf_components, windows)

    @pytest.fixture(scope='class')
    def action_potential_plots(self, planner, windows):
        return planner.add_stage(WaveformPlot(mode=WaveformPlotMode.INDIVIDUAL, alpha=0.4, row=schema.TRACK), windows)

    def test_execute(self, executor, planner, action_potential_plots):
        executor.execute(planner.get_plan())

