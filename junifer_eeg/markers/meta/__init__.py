"""Provide the EEG meta markers (computed from other markers)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .ratio import (
    EEGRatio,
    EEGRatioScalar,
    EEGRatioTimeseries,
    EEGRatioTopography,
    Ratio,
    RatioOperand,
)


__all__ = [
    "EEGRatio",
    "EEGRatioScalar",
    "EEGRatioTimeseries",
    "EEGRatioTopography",
    "Ratio",
    "RatioOperand",
]
