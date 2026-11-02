"""Provide the testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.pipeline import PipelineComponentRegistry

from .datagrabbers import TUEGTestingDataGrabber


# Register the testing DataGrabbers
PipelineComponentRegistry().register(
    step="datagrabber",
    klass=TUEGTestingDataGrabber,
)
