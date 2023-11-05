from pathlib import Path

import pytest


TESTDATA_ROOT = Path('.') / 'tests' / 'testdata'
"""Root dir of the testadata, relative to package root."""
DAPSYS_TESTDATA_ROOT = TESTDATA_ROOT / 'dapsys'
DAPSYS_TESTDATA_GLOB = "*.dps"
SPIKE2_TESTDATA_ROOT = TESTDATA_ROOT / 'spike2'
SPIKE2_TESTDATA_GLOB = "*.mat"



def pytest_generate_tests(metafunc):
    """ This allows us to load tests from external files by
    parametrizing tests with each test case found in the testdata folder
    """
    for fixture in metafunc.fixturenames:
        if fixture.startswith('file_'):
            if 'dapsys' in fixture:
                print(DAPSYS_TESTDATA_ROOT.absolute())
                tests = list(DAPSYS_TESTDATA_ROOT.rglob(DAPSYS_TESTDATA_GLOB))
                print(fixture, tests)
                metafunc.parametrize(fixture, tests, scope="class")
            elif 'spike2' in fixture:
                tests = list(SPIKE2_TESTDATA_ROOT.rglob(SPIKE2_TESTDATA_GLOB))
                print(fixture, tests)
                metafunc.parametrize(fixture, tests , scope="class")


