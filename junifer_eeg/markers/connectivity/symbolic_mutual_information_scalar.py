"""Provide class for the wSMI markers, reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..scalar_mixin import ScalarMixin
from .symbolic_mutual_information_base import EEGSymbolicMutualInformation


__all__ = ["EEGSymbolicMutualInformationScalar"]


@register_marker
class EEGSymbolicMutualInformationScalar(
    ScalarMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to scalars.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.ScalarMixin`.

    """
