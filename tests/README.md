# End-to-End tests
The test-suites here construct an analysis flow with each reader function and all compatible function-modules. Spike2 tests currently only load data, as its output is not compatible with any of the implemented modules.

## Preqrequisites
* Install the module with the dependecies from the dev group
* Place testdata in the appropriate directories. These directories may be links. Testdata is recoursively discovered based on the glob in this modules `conftest.py`. Recursive links are not followed due to limitations in Python's `pathlib` module.
  * Spike2:`./test/testdata/spike2`(relative to repository root)
  * DAPSYS: `./test/testdata/dapsys`(relative to repository root)

## Run the tests
Run the tests with pytest: `pytest -v -k e2e` (note that you may have to switch into the poetry environment with `poetry shell`).
The `-v` flag toggles verbose mode and is useful for this kind of tests, as it will print the name of the file the test is currently working on.

To only run DAPSYS e2e tests use `pytest -v -k "e2e and dapsys"`. 



