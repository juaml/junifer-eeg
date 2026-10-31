"""Provide the spectral EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from ._psd_estimator import PSDEstimator, PSDEstimatorParams
from .power_spectral_density import (
    EEGPowerSpectralDensity,
    EEGPowerSpectralDensityScalar,
    EEGPowerSpectralDensityTimeseries,
    EEGPowerSpectralDensityTopography,
)


__all__ = [
    "EEGPowerSpectralDensity",
    "EEGPowerSpectralDensityScalar",
    "EEGPowerSpectralDensityTimeseries",
    "EEGPowerSpectralDensityTopography",
    "PSDEstimator",
    "PSDEstimatorParams",
]
