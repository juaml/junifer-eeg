"""Provide the EEG event-related markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .contingent_negative_variation_base import EEGContingentNegativeVariation
from .contingent_negative_variation_scalar import EEGContingentNegativeVariationScalar
from .contingent_negative_variation_timeseries import EEGContingentNegativeVariationTimeseries
from .contingent_negative_variation_topography import EEGContingentNegativeVariationTopography
from .contrast import Contrast
from .event_related_contrast_base import EEGEventRelatedContrast
from .event_related_contrast_scalar import EEGEventRelatedContrastScalar
from .event_related_contrast_topography import EEGEventRelatedContrastTopography
from .event_related_potential_base import EEGEventRelatedPotential
from .event_related_potential_scalar import EEGEventRelatedPotentialScalar
from .event_related_potential_topography import EEGEventRelatedPotentialTopography
from .window import Window


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
