"""Provide class for the KC markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .kolmogorov_complexity_base import EEGKolmogorovComplexity


__all__ = ["EEGKolmogorovComplexityScalar"]


@register_marker
class EEGKolmogorovComplexityScalar(ScalarMixin, EEGKolmogorovComplexity):
    """Class for the KC markers, reduced to scalars.

    See :class:`.EEGKolmogorovComplexity` and :class:`.ScalarMixin`.

    """
