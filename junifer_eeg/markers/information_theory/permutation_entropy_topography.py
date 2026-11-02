"""Provide class for the PE markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .permutation_entropy_base import EEGPermutationEntropy


__all__ = ["EEGPermutationEntropyTopography"]


@register_marker
class EEGPermutationEntropyTopography(TopographyMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to topographies.

    See :class:`.EEGPermutationEntropy` and :class:`.TopographyMixin`.

    """
