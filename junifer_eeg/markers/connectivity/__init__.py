"""Provide the connectivity EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from ._smi_estimator import SMIEstimator, SMIEstimatorParams
from .spectral_connectivity import (
    EEGPhaseLockingValue,
    EEGPhaseLockingValueScalar,
    EEGPhaseLockingValueTopography,
    EEGSpectralConnectivity,
    EEGWeightedPhaseLagIndex,
    EEGWeightedPhaseLagIndexScalar,
    EEGWeightedPhaseLagIndexTopography,
)
from .symbolic_mutual_information import (
    EEGSymbolicMutualInformation,
    EEGSymbolicMutualInformationScalar,
    EEGSymbolicMutualInformationTimeseries,
    EEGSymbolicMutualInformationTopography,
)


__all__ = [
    "EEGPhaseLockingValue",
    "EEGPhaseLockingValueScalar",
    "EEGPhaseLockingValueTopography",
    "EEGSpectralConnectivity",
    "EEGSymbolicMutualInformation",
    "EEGSymbolicMutualInformationScalar",
    "EEGSymbolicMutualInformationTimeseries",
    "EEGSymbolicMutualInformationTopography",
    "EEGWeightedPhaseLagIndex",
    "EEGWeightedPhaseLagIndexScalar",
    "EEGWeightedPhaseLagIndexTopography",
    "SMIEstimator",
    "SMIEstimatorParams",
]
