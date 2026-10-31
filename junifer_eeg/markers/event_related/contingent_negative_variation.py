"""Provide the contingent negative variation (CNV) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any

import numpy as np
from junifer.api.decorators import register_marker
from mne.defaults import DEFAULTS
from scipy import linalg

from ..base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from ..utils import get_epochs, get_picks, time_mask


__all__ = [
    "EEGContingentNegativeVariation",
    "EEGContingentNegativeVariationScalar",
    "EEGContingentNegativeVariationTimeseries",
    "EEGContingentNegativeVariationTopography",
]


class EEGContingentNegativeVariation(EEGBaseMarker):
    """Base class for the contingent negative variation (CNV) markers.

    The CNV is the slope of a linear regression of the signal over time, in
    the window between ``tmin`` and ``tmax``, for each epoch and channel. The
    signal is scaled to the usual units (µV for EEG), so the slope is in
    µV/s. Port of ``nice.markers.ContingentNegativeVariation``. The feature
    is ``cnv``.

    Parameters
    ----------
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    tmin: float | None = None
    tmax: float | None = None

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the CNV.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray
            The values, shape (n_epochs, n_channels, 1).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        epochs = get_epochs(input)
        picks = get_picks(epochs.info)
        times = epochs.times
        tmin = times[0] if self.tmin is None else self.tmin
        mask = time_mask(times, tmin, self.tmax)
        # Design: intercept and time from the start of the window
        design = np.c_[np.ones(mask.sum()), times[mask] - tmin]
        scalings = np.array(
            [
                DEFAULTS["scalings"][x]
                for x in epochs.get_channel_types(picks=picks)
            ]
        )
        data = epochs.get_data(picks=picks)[..., mask]
        n_epochs, n_channels, n_times = data.shape
        # Solve all the epochs and channels at once: (n_times, epochs * chs)
        y = (data * scalings[:, np.newaxis]).reshape(-1, n_times).T
        betas, _, _, _ = linalg.lstsq(design, y)
        slopes = betas[1].reshape(n_epochs, n_channels)
        ch_names = [epochs.ch_names[x] for x in picks]
        return slopes[..., np.newaxis], ["cnv"], ch_names


@register_marker
class EEGContingentNegativeVariationScalar(
    ScalarMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to scalars.

    See :class:`.EEGContingentNegativeVariation` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGContingentNegativeVariationTopography(
    TopographyMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to topographies.

    See :class:`.EEGContingentNegativeVariation` and
    :class:`.TopographyMixin`.

    """


@register_marker
class EEGContingentNegativeVariationTimeseries(
    TimeseriesMixin, EEGContingentNegativeVariation
):
    """Class for the CNV markers, reduced to one value per epoch.

    See :class:`.EEGContingentNegativeVariation` and
    :class:`.TimeseriesMixin`.

    """
