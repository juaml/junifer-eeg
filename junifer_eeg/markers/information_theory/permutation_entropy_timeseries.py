"""Provide class for the PE markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .permutation_entropy_base import EEGPermutationEntropy


__all__ = ["EEGPermutationEntropyTimeseries"]


@register_marker
class EEGPermutationEntropyTimeseries(TimeseriesMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to one value per epoch.

    See :class:`.EEGPermutationEntropy` and :class:`.TimeseriesMixin`.

    """
