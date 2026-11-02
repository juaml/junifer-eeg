"""Provide class for estimating the PSD of epochs."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

import json
from functools import lru_cache
from typing import ClassVar

import mne
import numpy as np
import structlog
from junifer.typing import Dependencies
from junifer.utils import raise_error
from junifer.utils.singleton import Singleton
from scipy.signal import welch

from ..utils import DataRef, get_picks, time_mask
from ._psd_estimator_params import PSDEstimatorParams


__all__ = ["PSDEstimator"]


_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="markers", step="marker")


class PSDEstimator(metaclass=Singleton):
    """Class for estimating the PSD of epochs.

    It's designed as a singleton with caching, so the markers with the same
    estimator parameters compute the PSD of the data of an element once. The
    cache only keeps the last PSD, to limit the memory use.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"mne", "numpy", "scipy"}

    def __del__(self) -> None:
        """Terminate the class."""
        self._compute.cache_clear()

    def compute(
        self, epochs: mne.BaseEpochs, params: PSDEstimatorParams
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Compute the PSD.

        Parameters
        ----------
        epochs : mne.BaseEpochs
            The epochs.
        params : PSDEstimatorParams
            The parameters of the estimation.

        Returns
        -------
        numpy.ndarray
            The PSD, shape (n_epochs, n_channels, n_freqs).
        numpy.ndarray
            The frequencies.
        list of str
            The names of the channels.

        """
        return self._compute(
            DataRef(epochs), json.dumps(params.model_dump(), sort_keys=True)
        )

    @lru_cache(maxsize=1)  # noqa: B019
    def _compute(
        self, epochs_ref: DataRef, params_json: str
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Compute the PSD (cached)."""
        epochs = epochs_ref.obj
        params = PSDEstimatorParams(**json.loads(params_json))
        logger.debug(f"Computing PSD with {params_json}")
        method_params = params.method_params or {}
        sfreq = epochs.info["sfreq"]
        picks = get_picks(epochs.info)
        mask = time_mask(epochs.times, params.tmin, params.tmax, sfreq=sfreq)
        data = epochs.get_data(picks=picks)[:, :, mask]
        n_times = data.shape[-1]
        n_fft = method_params.get("n_fft", 256)
        nperseg = method_params.get("nperseg", 256)
        n_overlap = method_params.get("n_overlap", 0)
        # As in MNE: the segments cannot be longer than the data
        nperseg = min(nperseg, n_fft, n_times)
        if n_overlap >= nperseg:
            raise_error(
                f"n_overlap ({n_overlap}) must be smaller than nperseg "
                f"({nperseg})"
            )
        freqs, psds = welch(
            data,
            fs=sfreq,
            window="hamming",
            nperseg=nperseg,
            noverlap=n_overlap,
            nfft=n_fft,
            axis=-1,
        )
        fmax = sfreq / 2 if params.fmax is None else params.fmax
        freq_mask = (freqs >= params.fmin) & (freqs <= fmax)
        ch_names = [epochs.ch_names[x] for x in picks]
        return psds[..., freq_mask], freqs[freq_mask], ch_names
