"""Provide class for the KC markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .kolmogorov_complexity_base import EEGKolmogorovComplexity


__all__ = ["EEGKolmogorovComplexityTopography"]


@register_marker
class EEGKolmogorovComplexityTopography(
    TopographyMixin, EEGKolmogorovComplexity
):
    """Class for the KC markers, reduced to topographies.

    See :class:`.EEGKolmogorovComplexity` and :class:`.TopographyMixin`.

    """
