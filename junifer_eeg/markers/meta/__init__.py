"""Provide the EEG meta markers (computed from other markers)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .ratio_base import EEGRatio
from .ratio_scalar import EEGRatioScalar
from .ratio_timeseries import EEGRatioTimeseries
from .ratio_topography import EEGRatioTopography
from .ratio import Ratio
from .ratio_operand import RatioOperand


__all__ = [
    "EEGRatio",
    "EEGRatioScalar",
    "EEGRatioTimeseries",
    "EEGRatioTopography",
    "Ratio",
    "RatioOperand",
]
