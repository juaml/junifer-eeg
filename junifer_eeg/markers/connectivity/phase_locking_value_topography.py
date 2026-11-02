"""Provide class for the PLV markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .phase_locking_value_base import EEGPhaseLockingValue


__all__ = ["EEGPhaseLockingValueTopography"]


@register_marker
class EEGPhaseLockingValueTopography(TopographyMixin, EEGPhaseLockingValue):
    """Class for the PLV markers, reduced to topographies.

    See :class:`.EEGPhaseLockingValue` and :class:`.TopographyMixin`.

    """
