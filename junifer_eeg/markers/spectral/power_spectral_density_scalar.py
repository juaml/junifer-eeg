"""Provide class for the spectral markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .power_spectral_density_base import EEGPowerSpectralDensity


__all__ = ["EEGPowerSpectralDensityScalar"]


@register_marker
class EEGPowerSpectralDensityScalar(ScalarMixin, EEGPowerSpectralDensity):
    """Class for the spectral markers, reduced to scalars.

    See :class:`.EEGPowerSpectralDensity` and :class:`.ScalarMixin`.

    """
