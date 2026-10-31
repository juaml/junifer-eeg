"""Provide the information theory EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .kolmogorov_complexity import (
    EEGKolmogorovComplexity,
    EEGKolmogorovComplexityScalar,
    EEGKolmogorovComplexityTimeseries,
    EEGKolmogorovComplexityTopography,
)
from .permutation_entropy import (
    EEGPermutationEntropy,
    EEGPermutationEntropyScalar,
    EEGPermutationEntropyTimeseries,
    EEGPermutationEntropyTopography,
)


__all__ = [
    "EEGKolmogorovComplexity",
    "EEGKolmogorovComplexityScalar",
    "EEGKolmogorovComplexityTimeseries",
    "EEGKolmogorovComplexityTopography",
    "EEGPermutationEntropy",
    "EEGPermutationEntropyScalar",
    "EEGPermutationEntropyTimeseries",
    "EEGPermutationEntropyTopography",
]
