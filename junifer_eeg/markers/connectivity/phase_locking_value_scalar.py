"""Provide class for the PLV markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .phase_locking_value_base import EEGPhaseLockingValue


__all__ = ["EEGPhaseLockingValueScalar"]


@register_marker
class EEGPhaseLockingValueScalar(ScalarMixin, EEGPhaseLockingValue):
    """Class for the PLV markers, reduced to scalars.

    See :class:`.EEGPhaseLockingValue` and :class:`.ScalarMixin`.

    """
