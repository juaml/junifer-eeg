"""Provide class for the ratio markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .ratio_base import EEGRatio


__all__ = ["EEGRatioTopography"]


@register_marker
class EEGRatioTopography(TopographyMixin, EEGRatio):
    """Class for the ratio markers, reduced to topographies.

    See :class:`.EEGRatio` and :class:`.TopographyMixin`.

    """
