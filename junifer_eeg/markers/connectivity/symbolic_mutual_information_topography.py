"""Provide class for the wSMI markers, reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..topography_mixin import TopographyMixin
from .symbolic_mutual_information_base import EEGSymbolicMutualInformation


__all__ = ["EEGSymbolicMutualInformationTopography"]


@register_marker
class EEGSymbolicMutualInformationTopography(
    TopographyMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to topographies.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.TopographyMixin`.

    """
