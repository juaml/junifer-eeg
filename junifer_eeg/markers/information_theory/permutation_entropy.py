"""Provide the permutation entropy (PE) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import math
from typing import Any

import numpy as np
from junifer.api.decorators import register_marker

from ..base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from ..symbolic import symbolize
from ..utils import get_epochs, get_picks, lowpass_epochs, time_mask


__all__ = [
    "EEGPermutationEntropy",
    "EEGPermutationEntropyScalar",
    "EEGPermutationEntropyTimeseries",
    "EEGPermutationEntropyTopography",
]


class EEGPermutationEntropy(EEGBaseMarker):
    """Base class for the permutation entropy (PE) markers.

    The epochs are low-passed at ``filter_freq`` and transformed into
    symbols (see :func:`.symbolize`). The PE is the entropy of the
    distribution of the symbols in each epoch and channel, divided by its
    maximum. Port of ``nice.markers.PermutationEntropy``. The feature is
    ``pe``.

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

    tmin: float | None = None
    tmax: float | None = None
    kernel: int = 3
    tau: int = 8
    filter_freq: float | None = None

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the PE.

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
        sfreq = epochs.info["sfreq"]
        picks = get_picks(epochs.info)
        filter_freq = self.filter_freq
        if filter_freq is None:
            filter_freq = sfreq / self.kernel / self.tau
        data = lowpass_epochs(epochs.get_data(picks=picks), sfreq, filter_freq)
        data = data[..., time_mask(epochs.times, self.tmin, self.tmax)]
        n_symbols = math.factorial(self.kernel)
        pe = np.empty(data.shape[:2])
        for i_epoch, epoch in enumerate(data):
            symbols = symbolize(epoch, self.kernel, self.tau)
            counts = np.stack(
                [np.bincount(x, minlength=n_symbols) for x in symbols]
            )
            probs = counts / symbols.shape[-1]
            with np.errstate(divide="ignore", invalid="ignore"):
                pe[i_epoch] = np.nan_to_num(
                    -np.nansum(probs * np.log(probs), axis=-1)
                )
        pe /= np.log(n_symbols)
        ch_names = [epochs.ch_names[x] for x in picks]
        return pe[..., np.newaxis], ["pe"], ch_names


@register_marker
class EEGPermutationEntropyScalar(ScalarMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to scalars.

    See :class:`.EEGPermutationEntropy` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGPermutationEntropyTopography(TopographyMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to topographies.

    See :class:`.EEGPermutationEntropy` and :class:`.TopographyMixin`.

    """


@register_marker
class EEGPermutationEntropyTimeseries(TimeseriesMixin, EEGPermutationEntropy):
    """Class for the PE markers, reduced to one value per epoch.

    See :class:`.EEGPermutationEntropy` and :class:`.TimeseriesMixin`.

    """
