"""Provide EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .aggregation import AggregationStep, get_aggregation_function
from .base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from .connectivity import (
    EEGSymbolicMutualInformation,
    EEGSymbolicMutualInformationScalar,
    EEGSymbolicMutualInformationTimeseries,
    EEGSymbolicMutualInformationTopography,
    SMIEstimator,
    SMIEstimatorParams,
)
from .information_theory import (
    EEGKolmogorovComplexity,
    EEGKolmogorovComplexityScalar,
    EEGKolmogorovComplexityTimeseries,
    EEGKolmogorovComplexityTopography,
    EEGPermutationEntropy,
    EEGPermutationEntropyScalar,
    EEGPermutationEntropyTimeseries,
    EEGPermutationEntropyTopography,
)
from .spectral import (
    EEGPowerSpectralDensity,
    EEGPowerSpectralDensityScalar,
    EEGPowerSpectralDensityTimeseries,
    EEGPowerSpectralDensityTopography,
    PSDEstimator,
    PSDEstimatorParams,
)


__all__ = [
    "AggregationStep",
    "EEGBaseMarker",
    "EEGKolmogorovComplexity",
    "EEGKolmogorovComplexityScalar",
    "EEGKolmogorovComplexityTimeseries",
    "EEGKolmogorovComplexityTopography",
    "EEGPermutationEntropy",
    "EEGPermutationEntropyScalar",
    "EEGPermutationEntropyTimeseries",
    "EEGPermutationEntropyTopography",
    "EEGPowerSpectralDensity",
    "EEGPowerSpectralDensityScalar",
    "EEGPowerSpectralDensityTimeseries",
    "EEGPowerSpectralDensityTopography",
    "EEGSymbolicMutualInformation",
    "EEGSymbolicMutualInformationScalar",
    "EEGSymbolicMutualInformationTimeseries",
    "EEGSymbolicMutualInformationTopography",
    "PSDEstimator",
    "PSDEstimatorParams",
    "SMIEstimator",
    "SMIEstimatorParams",
    "ScalarMixin",
    "TimeseriesMixin",
    "TopographyMixin",
    "get_aggregation_function",
]
