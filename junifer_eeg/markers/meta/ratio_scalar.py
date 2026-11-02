"""Provide class for the ratio markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .ratio_base import EEGRatio


__all__ = ["EEGRatioScalar"]


@register_marker
class EEGRatioScalar(ScalarMixin, EEGRatio):
    """Class for the ratio markers, reduced to scalars.

    See :class:`.EEGRatio` and :class:`.ScalarMixin`.

    """
