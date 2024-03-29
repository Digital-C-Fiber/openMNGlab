# Release Checklist
## preqrequisites
* have poetry installed
* poetry is setup to use with PyPI ([instructions](https://python-poetry.org/docs/repositories/#publishable-repositories))

## steps
1. pull latest main
2. checkout main
3. run pytest. Do not continue if tests fail.
4. run `poetry version {rule}` ([command doc](https://python-poetry.org/docs/cli/#version)) to bump the version spec in `pyproject.toml` acoording to the rule.
    * While in unstable verisoning schema (`0.*`) use following rules:
      * `patch` for patches (e.g., fixing stuff, upgrading dependencies to new patch or minor version)
      * `minor` for anything else
5. update the `CITATION.cff`: 
   * update the version number
   * update the release date
6. commit the changes made to `pyproject.toml` and `CITATION.cff`
7. create a new tag containing the new version on this commit, prefixed with a "v" (e.g., `v0.3.1`)
8. push the commit and the tag to `main`
9. use `poetry build` to build the package. The build artificats are usually found in (`./dist`)
10. use `poetry publish` to publish to PyPI
11. On GitHub, create a new release from the version tag:
    1. Go to "releases"
    2. "Draft new release"
    3. choose the tag
    4. enter release title and patchnotes
    5. attach the build artifacts of this release
    6. "Set as latest release"
    7. Publish