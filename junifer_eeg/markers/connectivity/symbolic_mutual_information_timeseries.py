"""Provide class for the wSMI markers, reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from junifer.api.decorators import register_marker

from ..timeseries_mixin import TimeseriesMixin
from .symbolic_mutual_information_base import EEGSymbolicMutualInformation


__all__ = ["EEGSymbolicMutualInformationTimeseries"]


@register_marker
class EEGSymbolicMutualInformationTimeseries(
    TimeseriesMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to one value per epoch.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.TimeseriesMixin`.

    """
