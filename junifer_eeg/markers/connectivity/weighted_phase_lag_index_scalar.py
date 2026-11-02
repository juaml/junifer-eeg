"""Provide class for the wPLI markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .weighted_phase_lag_index_base import EEGWeightedPhaseLagIndex


__all__ = ["EEGWeightedPhaseLagIndexScalar"]


@register_marker
class EEGWeightedPhaseLagIndexScalar(ScalarMixin, EEGWeightedPhaseLagIndex):
    """Class for the wPLI markers, reduced to scalars.

    See :class:`.EEGWeightedPhaseLagIndex` and :class:`.ScalarMixin`.

    """
