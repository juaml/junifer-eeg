"""Provide class for the window decoding markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .window_decoding_base import EEGWindowDecoding


__all__ = ["EEGWindowDecodingScalar"]


@register_marker
class EEGWindowDecodingScalar(ScalarMixin, EEGWindowDecoding):
    """Class for the window decoding markers, reduced to scalars.

    See :class:`.EEGWindowDecoding` and :class:`.ScalarMixin`.

    """
