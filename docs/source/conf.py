# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
import tomllib
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'OpenMNGLab'
copyright = '2023, Peter Konradi'
author = 'Peter Konradi'

def get_pyproject_version():
    with (Path("..")/".."/"pyproject.toml").open('rb') as f:
        pyproject_toml = tomllib.load(f)
    ver_str = pyproject_toml["tool"]["poetry"]["version"]
    split_str = ver_str.split('.',2)
    release = split_str[2] if len(split_str) == 3 else ''
    version = ".".join(split_str[:2])
    return version, release

version, release = get_pyproject_version()
print(version, release)

sys.path.insert(0, os.path.abspath("../.."))


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosectionlabel', 'sphinx.ext.autosummary',
              'sphinx.ext.viewcode',
              'sphinx.ext.intersphinx',
              'sphinx.ext.napoleon',
               ]
autosummary_generate = True
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
