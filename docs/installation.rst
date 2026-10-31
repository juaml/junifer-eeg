.. include:: links.inc

Installing ``junifer-eeg``
==========================

We strongly recommend using
`virtual environments <https://realpython.com/python-virtual-environments-a-primer>`_.

From the source
---------------

.. code-block:: bash

    git clone https://github.com/juaml/junifer-eeg.git
    cd junifer-eeg
    pip install -e ".[dev]"

This installs `junifer`_, `MNE-Python`_ and the other dependencies.

.. note::

   ``junifer run`` uses the DataReader of the YAML (needed to read the EEG
   data type) since junifer 0.0.9 (juaml/junifer#538), currently a
   pre-release.

Building the documentation
--------------------------

.. code-block:: bash

    pip install -e ".[docs]"
    make -C docs local

The documentation is then in ``docs/_build``. ``make -C docs html`` builds
all the released versions and ``main`` with sphinx-polyversion, as published.
