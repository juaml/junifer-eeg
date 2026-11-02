"""Provide class for the spectral markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .power_spectral_density_base import EEGPowerSpectralDensity


__all__ = ["EEGPowerSpectralDensityTopography"]


@register_marker
class EEGPowerSpectralDensityTopography(
    TopographyMixin, EEGPowerSpectralDensity
):
    """Class for the spectral markers, reduced to topographies.

    See :class:`.EEGPowerSpectralDensity` and :class:`.TopographyMixin`.

    """
