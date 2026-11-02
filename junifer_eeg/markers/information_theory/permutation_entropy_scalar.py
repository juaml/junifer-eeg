"""Provide class for the PE markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .permutation_entropy_base import EEGPermutationEntropy


__all__ = ["EEGPermutationEntropyScalar"]


@register_marker
class EEGPermutationEntropyScalar(ScalarMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to scalars.

    See :class:`.EEGPermutationEntropy` and :class:`.ScalarMixin`.

    """
