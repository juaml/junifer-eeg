"""Provide class for the wPLI markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .weighted_phase_lag_index_base import EEGWeightedPhaseLagIndex


__all__ = ["EEGWeightedPhaseLagIndexTopography"]


@register_marker
class EEGWeightedPhaseLagIndexTopography(
    TopographyMixin, EEGWeightedPhaseLagIndex
):
    """Class for the wPLI markers, reduced to topographies.

    See :class:`.EEGWeightedPhaseLagIndex` and :class:`.TopographyMixin`.

    """
