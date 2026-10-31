"""Provide the symbolic mutual information (SMI) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar, Literal

import numpy as np
from junifer.api.decorators import register_marker

from ..aggregation import Axis
from ..base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from ..utils import get_epochs
from ._smi_estimator import SMIEstimator, SMIEstimatorParams


__all__ = [
    "EEGSymbolicMutualInformation",
    "EEGSymbolicMutualInformationScalar",
    "EEGSymbolicMutualInformationTimeseries",
    "EEGSymbolicMutualInformationTopography",
]


class EEGSymbolicMutualInformation(EEGBaseMarker):
    """Base class for the (weighted) symbolic mutual information markers.

    The current source density (CSD) of the epochs is computed (if ``csd``),
    low-passed at ``filter_freq`` and transformed into symbols (see
    :func:`.symbolize`). The SMI of each pair of channels is the mutual
    information of their symbols in each epoch, divided by the maximum
    entropy. The weighted SMI (wSMI) ignores the pairs of identical and
    opposite symbols. Port of ``nice.markers.SymbolicMutualInformation``. The
    feature is ``wsmi`` or ``smi``, and the values of a channel with itself
    are 0. The (w)SMI is computed once for the markers with the same
    parameters (see :class:`.SMIEstimator`).

    Parameters
    ----------
    tmin : float or None, optional
        The start of the epochs to use. If None, from the start
        (default None).
    tmax : float or None, optional
        The end of the epochs to use. If None, until the end (default None).
    kernel : int, optional
        The number of samples of each symbol (default 3).
    tau : int, optional
        The number of samples between the samples of each symbol
        (default 8).
    method : {"weighted", "smi"}, optional
        Whether to compute the wSMI or the SMI (default "weighted").
    csd : bool, optional
        Whether to compute the CSD first (default True).
    filter_freq : float or None, optional
        The low-pass frequency. If None, ``sfreq / kernel / tau``
        (default None).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _AXES: ClassVar[tuple[Axis, ...]] = ("epochs", "channels", "channels_y")

    tmin: float | None = None
    tmax: float | None = None
    kernel: int = 3
    tau: int = 8
    method: Literal["weighted", "smi"] = "weighted"
    csd: bool = True
    filter_freq: float | None = None

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the (w)SMI.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray
            The values, shape (n_epochs, n_channels, n_channels, 1).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        epochs = get_epochs(input)
        params = SMIEstimatorParams(
            tmin=self.tmin,
            tmax=self.tmax,
            kernel=self.kernel,
            tau=self.tau,
            method=self.method,
            csd=self.csd,
            filter_freq=self.filter_freq,
        )
        out, ch_names = SMIEstimator().compute(epochs, params)
        feature = "wsmi" if self.method == "weighted" else "smi"
        return out[..., np.newaxis], [feature], ch_names


@register_marker
class EEGSymbolicMutualInformationScalar(
    ScalarMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to scalars.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGSymbolicMutualInformationTopography(
    TopographyMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to topographies.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.TopographyMixin`.

    """


@register_marker
class EEGSymbolicMutualInformationTimeseries(
    TimeseriesMixin, EEGSymbolicMutualInformation
):
    """Class for the wSMI markers, reduced to one value per epoch.

    See :class:`.EEGSymbolicMutualInformation` and :class:`.TimeseriesMixin`.

    """
