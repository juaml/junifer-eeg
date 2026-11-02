"""Provide class for the event-related contrasts, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .event_related_contrast_base import EEGEventRelatedContrast


__all__ = ["EEGEventRelatedContrastTopography"]


@register_marker
class EEGEventRelatedContrastTopography(
    TopographyMixin, EEGEventRelatedContrast
):
    """Class for the event-related contrast markers, reduced to topographies.

    See :class:`.EEGEventRelatedContrast` and :class:`.TopographyMixin`.

    """
