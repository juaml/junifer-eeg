"""Provide configuration for Sphinx."""

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import os
from pathlib import Path

from setuptools_scm import get_version


# -- Path setup --------------------------------------------------------------

PROJECT_ROOT_DIR = Path(__file__).parents[1].resolve()

# -- Project information -----------------------------------------------------

github_url = "https://github.com"
github_repo_org = "juaml"
github_repo_name = "junifer-eeg"
github_repo_slug = f"{github_repo_org}/{github_repo_name}"
github_repo_url = f"{github_url}/{github_repo_slug}"

project = github_repo_name
author = f"{project} Contributors"
copyright = f"{datetime.date.today().year}, {author}"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # Built-in extensions:
    "sphinx.ext.autodoc",  # include documentation from docstrings
    "sphinx.ext.autosummary",  # generate autodoc summaries
    "sphinx.ext.extlinks",  # markup to shorten external links
    "sphinx.ext.intersphinx",  # link to other projects` documentation
    "sphinx.ext.mathjax",  # math support for HTML outputs in Sphinx
    # Third-party extensions:
    "numpydoc",  # support for NumPy style docstrings
    "sphinx_copybutton",  # copy button for code blocks
    "sphinxcontrib.autodoc_pydantic",  # autodoc support for pydantic models
    "myst_parser",  # include the Markdown changelog
    "enum_tools.autoenum",  # enum support
]

# Add any paths that contain templates here, relative to this directory.
templates_path = [
    "_templates",
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

nitpicky = True

nitpick_ignore_regex = [
    ("py:class", "numpy._typing.*"),
    ("py:class", "typing.Any"),
    ("py:obj", "junifer.*"),  # ignore junifer internal
    ("py:class", "junifer.*"),  # ignore junifer internal
    ("py:class", "annotated_types.*"),  # ignore pydantic annotated types
    ("py:class", "PydanticUndefined"),
    ("py:class", "FieldInfo"),
    ("py:class", "NoneType"),
    ("py:class", "DataRef"),  # internal cache key
]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = "junifer-eeg documentation"

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
    "css/version_selector.css",
]

html_js_files = [
    "js/custom.js",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "versions.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}

# -- sphinx.ext.autodoc configuration ----------------------------------------

autoclass_content = "both"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- autodoc_pydantic configuration ------------------------------------------

# The parameters are documented in the numpydoc docstrings
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_members = False
autodoc_pydantic_model_undoc_members = False

# -- Version information -----------------------------------------------------

# sphinx-polyversion is only imported (and needed) for multi-version builds;
# local builds get the version from setuptools-scm.
if os.getenv("POLYVERSION_DATA") is None:
    # If POLYVERSION_DATA is not set, we are likely building the docs locally.
    # In this case, we can use setuptools_scm to get the version information.
    release = get_version(
        root=PROJECT_ROOT_DIR,
        version_scheme="guess-next-dev",
        local_scheme="no-local-version",
    )
else:
    # Only needed (and installed) when building with sphinx-polyversion
    from sphinx_polyversion.api import load
    from sphinx_polyversion.git import GitRefType

    load(globals())
    # This adds the following to the global scope
    # html_context = {
    #     "revisions": [GitRef('main', ...), GitRef('v6.8.9', ...), ...],
    #     "current": GitRef('v1.4.6', ...),
    # }

    # process the loaded version information as you wish
    html_context = globals().get("html_context", {})

    if (
        html_context["current"].type_ == GitRefType.BRANCH
        and html_context["current"].name == "main"
    ):
        release = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_JUNIFER_EEG")
    else:
        release = html_context["current"].name

version = release

# -- sphinx.ext.autosummary configuration ------------------------------------

autosummary_generate = True

# -- sphinx.ext.intersphinx configuration ------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "junifer": ("https://juaml.github.io/junifer/main", None),
    "mne": ("https://mne.tools/stable/", None),
    "mne_connectivity": ("https://mne.tools/mne-connectivity/stable/", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# -- sphinx.ext.extlinks configuration ---------------------------------------

extlinks = {
    "gh": (f"{github_repo_url}/issues/%s", "#%s"),
}

# -- numpydoc configuration --------------------------------------------------

numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_xref_aliases = {
    "Path": "pathlib.Path",
    "Enum": "enum.Enum",
}
numpydoc_xref_ignore = {
    "of",
    "shape",
    "optional",
    "or",
    "the",
    "options",
    "function",
    "object",
    "class",
    "objects",
    "positive",
    "negative",
    "and",
}

# -- myst_parser configuration -----------------------------------------------

myst_heading_anchors = 2
# The changelog starts at the second heading level
suppress_warnings = ["myst.header"]
