"""Provide class for the ERP markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .event_related_potential_base import EEGEventRelatedPotential


__all__ = ["EEGEventRelatedPotentialScalar"]


@register_marker
class EEGEventRelatedPotentialScalar(ScalarMixin, EEGEventRelatedPotential):
    """Class for the ERP markers, reduced to scalars.

    See :class:`.EEGEventRelatedPotential` and :class:`.ScalarMixin`.

    """
