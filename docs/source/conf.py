# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from mops import __version__, __project_name__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = __project_name__
copyright = '2026, Podolian Vladimir'
author = 'Podolian Vladimir'

release = __version__
version = release


print('the path is: ', sys.path[0])


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autodoc.typehints',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

source_dirs = ['../../mops']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
    'pillow': ('https://pillow.readthedocs.io/en/stable/', None),
    'appium': ('https://appium.github.io/python-client-sphinx/', None),
    'selenium': ('https://www.selenium.dev/selenium/docs/api/py/', None),
    # 'playwright': ('https://playwright.dev/python/docs', None),
}

intersphinx_disabled_domains = ['std']
autodoc_member_order = 'bysource'

templates_path = ['_templates']
html_static_path = ['_static']

source_suffix = ['.rst', '.md']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_theme_options = {
    "light_logo": "dark_logo.png",
    "dark_logo": "transparent_logo.png",
}

# sphinx.ext.viewcode
# https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
viewcode_line_numbers = True  # Enable line numbers in the source code

# -- Options for EPUB output
epub_show_urls = 'footnote'
