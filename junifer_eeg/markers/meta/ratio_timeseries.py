"""Provide class for the ratio markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .ratio_base import EEGRatio


__all__ = ["EEGRatioTimeseries"]


@register_marker
class EEGRatioTimeseries(TimeseriesMixin, EEGRatio):
    """Class for the ratio markers, reduced to timeseries.

    See :class:`.EEGRatio` and :class:`.TimeseriesMixin`.

    """
