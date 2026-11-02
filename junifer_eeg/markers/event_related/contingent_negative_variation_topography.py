"""Provide class for the CNV markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .contingent_negative_variation_base import EEGContingentNegativeVariation


__all__ = ["EEGContingentNegativeVariationTopography"]


@register_marker
class EEGContingentNegativeVariationTopography(
    TopographyMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to topographies.

    See :class:`.EEGContingentNegativeVariation` and
    :class:`.TopographyMixin`.

    """
