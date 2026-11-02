"""Provide class for the event-related contrasts, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .event_related_contrast_base import EEGEventRelatedContrast


__all__ = ["EEGEventRelatedContrastScalar"]


@register_marker
class EEGEventRelatedContrastScalar(ScalarMixin, EEGEventRelatedContrast):
    """Class for the event-related contrast markers, reduced to scalars.

    See :class:`.EEGEventRelatedContrast` and :class:`.ScalarMixin`.

    """
