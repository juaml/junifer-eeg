"""Provide class for the ERP markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .event_related_potential_base import EEGEventRelatedPotential


__all__ = ["EEGEventRelatedPotentialTopography"]


@register_marker
class EEGEventRelatedPotentialTopography(
    TopographyMixin, EEGEventRelatedPotential
):
    """Class for the ERP markers, reduced to topographies.

    See :class:`.EEGEventRelatedPotential` and :class:`.TopographyMixin`.

    """
