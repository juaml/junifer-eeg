"""Provide class for the KC markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .kolmogorov_complexity_base import EEGKolmogorovComplexity


__all__ = ["EEGKolmogorovComplexityTimeseries"]


@register_marker
class EEGKolmogorovComplexityTimeseries(
    TimeseriesMixin, EEGKolmogorovComplexity
):
    """Class for the KC markers, reduced to one value per epoch.

    See :class:`.EEGKolmogorovComplexity` and :class:`.TimeseriesMixin`.

    """
