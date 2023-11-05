from pathlib import Path

import pytest


TESTDATA_ROOT = Path('.') / 'tests' / 'testdata'
"""Root dir of the testadata, relative to package root."""

TESTDATA_DICT = {"dapsys": (TESTDATA_ROOT / 'dapsys', "*.dps"), "spike2": (TESTDATA_ROOT / 'spike2', "*.mat")}




def pytest_generate_tests(metafunc):
    """ This allows us to load tests from external files by
    parametrizing tests with each test case found in the testdata folder
    """
    for fixture in metafunc.fixturenames:
        if fixture.startswith('file_'):
            for k, (data_root, data_glob) in TESTDATA_DICT.items():
                if k in fixture:
                    tests = list(data_root.rglob(data_glob))
                    metafunc.parametrize(fixture, tests, scope="class", ids=[p.name for p in tests])


