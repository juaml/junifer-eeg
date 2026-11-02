"""Provide class for the spectral markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .power_spectral_density_base import EEGPowerSpectralDensity


__all__ = ["EEGPowerSpectralDensityTimeseries"]


@register_marker
class EEGPowerSpectralDensityTimeseries(
    TimeseriesMixin, EEGPowerSpectralDensity
):
    """Class for the spectral markers, reduced to one value per epoch.

    See :class:`.EEGPowerSpectralDensity` and :class:`.TimeseriesMixin`.

    """
