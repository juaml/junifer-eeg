"""Provide the Kolmogorov complexity (KC) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import zlib
from typing import Any

import numpy as np
from junifer.api.decorators import register_marker
from junifer.utils import raise_error

from ..base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from ..utils import get_epochs, get_picks, time_mask


__all__ = [
    "EEGKolmogorovComplexity",
    "EEGKolmogorovComplexityScalar",
    "EEGKolmogorovComplexityTimeseries",
    "EEGKolmogorovComplexityTopography",
]


class EEGKolmogorovComplexity(EEGBaseMarker):
    """Base class for the Kolmogorov complexity (KC) markers.

    Each epoch and channel is discretized in ``nbins`` amplitude bins, and
    the KC is approximated by the compression ratio (with zlib) of the
    sequence of bins. Port of ``nice.markers.KolmogorovComplexity``. The
    feature is ``kc``.

    Parameters
    ----------
    tmin : float or None, optional
        The start of the epochs to use. If None, from the start
        (default None).
    tmax : float or None, optional
        The end of the epochs to use. If None, until the end (default None).
    nbins : int, optional
        The number of amplitude bins (default 32).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    tmin: float | None = None
    tmax: float | None = None
    nbins: int = 32

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        if not 1 < self.nbins <= 256:
            raise_error("`nbins` must be between 2 and 256")

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the KC.

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
        data = epochs.get_data(picks=picks)
        data = data[..., time_mask(epochs.times, self.tmin, self.tmax)]
        symbols = _discretize(data, self.nbins)
        kc = np.empty(data.shape[:2])
        n_times = data.shape[-1]
        for i_epoch, i_channel in np.ndindex(*kc.shape):
            string = symbols[i_epoch, i_channel].tobytes()
            kc[i_epoch, i_channel] = len(zlib.compress(string)) / n_times
        ch_names = [epochs.ch_names[x] for x in picks]
        return kc[..., np.newaxis], ["kc"], ch_names


def _discretize(data: np.ndarray, nbins: int) -> np.ndarray:
    """Discretize signals in amplitude bins (as in NICE).

    The bins span between the 10th and 90th percentiles (by rank) of each
    signal. The values outside are assigned to the first and last bins.

    Parameters
    ----------
    data : numpy.ndarray
        The signals, shape (..., n_times).
    nbins : int
        The number of bins.

    Returns
    -------
    numpy.ndarray
        The bins, as the characters from "A", shape (..., n_times).

    """
    n_times = data.shape[-1]
    sorted_data = np.sort(data, axis=-1)
    first = int(n_times / 10)
    last = n_times - first if first > 1 else n_times - 1
    lower = sorted_data[..., first, np.newaxis]
    upper = sorted_data[..., last, np.newaxis]
    bin_size = (upper - lower) / nbins
    bins = np.trunc((data - lower) / bin_size)
    bins = np.clip(bins, 0, nbins - 1).astype(np.uint8)
    return bins + ord("A")


@register_marker
class EEGKolmogorovComplexityScalar(ScalarMixin, EEGKolmogorovComplexity):
    """Class for the KC markers, reduced to scalars.

    See :class:`.EEGKolmogorovComplexity` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGKolmogorovComplexityTopography(
    TopographyMixin, EEGKolmogorovComplexity
):
    """Class for the KC markers, reduced to topographies.

    See :class:`.EEGKolmogorovComplexity` and :class:`.TopographyMixin`.

    """


@register_marker
class EEGKolmogorovComplexityTimeseries(
    TimeseriesMixin, EEGKolmogorovComplexity
):
    """Class for the KC markers, reduced to one value per epoch.

    See :class:`.EEGKolmogorovComplexity` and :class:`.TimeseriesMixin`.

    """
