"""Provide class for the CNV markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .contingent_negative_variation_base import EEGContingentNegativeVariation


__all__ = ["EEGContingentNegativeVariationScalar"]


@register_marker
class EEGContingentNegativeVariationScalar(
    ScalarMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to scalars.

    See :class:`.EEGContingentNegativeVariation` and :class:`.ScalarMixin`.

    """
