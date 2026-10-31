"""Provide the estimator of the power spectral density (PSD)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import json
from functools import lru_cache
from typing import Any, ClassVar, Literal

import mne
import numpy as np
import structlog
from junifer.typing import Dependencies
from junifer.utils import raise_error
from junifer.utils.singleton import Singleton
from pydantic import BaseModel, ConfigDict
from scipy.signal import welch

from ..utils import DataRef, get_picks, time_mask


__all__ = ["PSDEstimator", "PSDEstimatorParams"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="markers", step="marker")


class PSDEstimatorParams(BaseModel):
    """Parameters of the PSD estimation.

    Parameters
    ----------
    method : {"welch"}, optional
        The method (default "welch").
    tmin : float or None, optional
        The start of the epochs to use. If None, from the start
        (default None).
    tmax : float or None, optional
        The end of the epochs to use. If None, until the end (default None).
    fmin : float, optional
        The minimum frequency (default 0.0).
    fmax : float or None, optional
        The maximum frequency. If None, the Nyquist frequency (default None).
    method_params : dict or None, optional
        The parameters of the method. For ``welch``: ``n_fft`` (default
        256), ``nperseg`` (default 256) and ``n_overlap`` (default 0). The
        segments are zero-padded to ``n_fft``, as in MNE (default None).

    """

    model_config = ConfigDict(extra="forbid")

    method: Literal["welch"] = "welch"
    tmin: float | None = None
    tmax: float | None = None
    fmin: float = 0.0
    fmax: float | None = None
    method_params: dict[str, Any] | None = None


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
