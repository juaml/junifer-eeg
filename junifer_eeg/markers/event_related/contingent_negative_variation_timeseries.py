"""Provide class for the CNV markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .contingent_negative_variation_base import EEGContingentNegativeVariation


__all__ = ["EEGContingentNegativeVariationTimeseries"]


@register_marker
class EEGContingentNegativeVariationTimeseries(
    TimeseriesMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to one value per epoch.

    See :class:`.EEGContingentNegativeVariation` and
    :class:`.TimeseriesMixin`.

    """
