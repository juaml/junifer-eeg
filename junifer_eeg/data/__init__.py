"""Provide pipeline data for EEG."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .rois import EEGROIRegistry, get_roi_channels


__all__ = ["EEGROIRegistry", "get_roi_channels"]
