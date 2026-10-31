"""Provide the EEG event-related markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .contingent_negative_variation import (
    EEGContingentNegativeVariation,
    EEGContingentNegativeVariationScalar,
    EEGContingentNegativeVariationTimeseries,
    EEGContingentNegativeVariationTopography,
)
from .event_related_contrast import (
    Contrast,
    EEGEventRelatedContrast,
    EEGEventRelatedContrastScalar,
    EEGEventRelatedContrastTopography,
)
from .event_related_potential import (
    EEGEventRelatedPotential,
    EEGEventRelatedPotentialScalar,
    EEGEventRelatedPotentialTopography,
    Window,
)


__all__ = [
    "Contrast",
    "EEGContingentNegativeVariation",
    "EEGContingentNegativeVariationScalar",
    "EEGContingentNegativeVariationTimeseries",
    "EEGContingentNegativeVariationTopography",
    "EEGEventRelatedContrast",
    "EEGEventRelatedContrastScalar",
    "EEGEventRelatedContrastTopography",
    "EEGEventRelatedPotential",
    "EEGEventRelatedPotentialScalar",
    "EEGEventRelatedPotentialTopography",
    "Window",
]
