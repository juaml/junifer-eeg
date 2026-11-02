"""junifer EEG."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

# The components register themselves in junifer when imported, so they are
# imported eagerly (`with: junifer_eeg` in the YAML). The data type must be
# registered first, as the other components use it.
from . import datatypes
from . import data
from . import datareader
from . import preprocess
from . import markers
from ._version import __version__
