"""Provide the estimator of the symbolic mutual information (SMI)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

import json
import math
from functools import lru_cache
from typing import ClassVar, Literal

import mne
import numpy as np
import structlog
from junifer.typing import Dependencies
from junifer.utils.singleton import Singleton
from pydantic import BaseModel, ConfigDict

from ..symbolic import symbol_weights, symbolize
from ..utils import DataRef, get_picks, lowpass_epochs, time_mask


__all__ = ["SMIEstimator", "SMIEstimatorParams"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="markers", step="marker")


class SMIEstimatorParams(BaseModel):
    """Parameters of the (w)SMI estimation.

    See :class:`.EEGSymbolicMutualInformation` for the parameters.

    """

    model_config = ConfigDict(extra="forbid")

    tmin: float | None = None
    tmax: float | None = None
    kernel: int = 3
    tau: int = 8
    method: Literal["weighted", "smi"] = "weighted"
    csd: bool = True
    filter_freq: float | None = None


class SMIEstimator(metaclass=Singleton):
    """Class for estimating the (w)SMI of epochs.

    It's designed as a singleton with caching, so the markers with the same
    parameters (e.g., the scalars and the topographies) compute the (w)SMI of
    the data of an element once. The cache only keeps the last (w)SMI, to
    limit the memory use.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"mne", "numpy", "scipy"}

    def __del__(self) -> None:
        """Terminate the class."""
        self._compute.cache_clear()

    def compute(
        self, epochs: mne.BaseEpochs, params: SMIEstimatorParams
    ) -> tuple[np.ndarray, list[str]]:
        """Compute the (w)SMI.

        Parameters
        ----------
        epochs : mne.BaseEpochs
            The epochs.
        params : SMIEstimatorParams
            The parameters of the estimation.

        Returns
        -------
        numpy.ndarray
            The (w)SMI, shape (n_epochs, n_channels, n_channels).
        list of str
            The names of the channels.

        """
        return self._compute(
            DataRef(epochs), json.dumps(params.model_dump(), sort_keys=True)
        )

    @lru_cache(maxsize=1)  # noqa: B019
    def _compute(
        self, epochs_ref: DataRef, params_json: str
    ) -> tuple[np.ndarray, list[str]]:
        """Compute the (w)SMI (cached)."""
        epochs = epochs_ref.obj
        params = SMIEstimatorParams(**json.loads(params_json))
        logger.debug(f"Computing SMI with {params_json}")
        if params.csd:
            epochs = mne.preprocessing.compute_current_source_density(
                epochs, lambda2=1e-5, verbose="error"
            )
        picks = get_picks(epochs.info, csd=params.csd)
        sfreq = epochs.info["sfreq"]
        filter_freq = params.filter_freq
        if filter_freq is None:
            filter_freq = sfreq / params.kernel / params.tau
        data = lowpass_epochs(epochs.get_data(picks=picks), sfreq, filter_freq)
        data = data[..., time_mask(epochs.times, params.tmin, params.tmax)]
        n_symbols = math.factorial(params.kernel)
        weights = symbol_weights(n_symbols)
        if params.method == "smi":
            weights = np.ones_like(weights)
        n_epochs, n_channels, _ = data.shape
        out = np.empty((n_epochs, n_channels, n_channels))
        for i_epoch, epoch in enumerate(data):
            symbols = symbolize(epoch, params.kernel, params.tau)
            out[i_epoch] = _weighted_mi(symbols, n_symbols, weights)
        out /= np.log(n_symbols)
        ch_names = [epochs.ch_names[x] for x in picks]
        return out, ch_names


def _weighted_mi(
    symbols: np.ndarray, n_symbols: int, weights: np.ndarray
) -> np.ndarray:
    """Compute the weighted mutual information of each pair of signals.

    Parameters
    ----------
    symbols : numpy.ndarray
        The symbols of each signal, shape (n_channels, n_times).
    n_symbols : int
        The number of symbols.
    weights : numpy.ndarray
        The weight of each pair of symbols, shape (n_symbols, n_symbols).

    Returns
    -------
    numpy.ndarray
        The weighted mutual information, shape (n_channels, n_channels), 0 in
        the diagonal.

    """
    n_channels, n_times = symbols.shape
    # One-hot encoding, shape (n_channels * n_symbols, n_times)
    onehot = np.zeros((n_channels, n_symbols, n_times))
    np.put_along_axis(onehot, symbols[:, np.newaxis, :], 1.0, axis=1)
    onehot = onehot.reshape(n_channels * n_symbols, n_times)
    # Joint and marginal probabilities
    pxy = (onehot @ onehot.T) / n_times
    pxy = pxy.reshape(n_channels, n_symbols, n_channels, n_symbols)
    px = onehot.reshape(n_channels, n_symbols, n_times).mean(axis=-1)
    denominator = (
        px[:, :, np.newaxis, np.newaxis] * px[np.newaxis, np.newaxis, :, :]
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(pxy > 0, pxy * np.log(pxy / denominator), 0.0)
    out = np.einsum("aibj,ij->ab", terms, weights)
    np.fill_diagonal(out, 0.0)
    return out
