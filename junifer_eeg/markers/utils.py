"""Provide utilities for the EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import mne
import numpy as np
from junifer.utils import raise_error
from scipy.signal import butter, filtfilt


__all__ = [
    "DataRef",
    "get_epochs",
    "get_picks",
    "lowpass_epochs",
    "time_mask",
]


class DataRef:
    """Reference to an object, hashed by identity (for caching).

    The data of an element is the same object for all the markers, so the
    estimators cache their results by its identity. The cache keeps a
    reference to the object, so its ``id`` is not reused while it is cached.

    Parameters
    ----------
    obj : object
        The object.

    """

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def __hash__(self) -> int:
        """Hash by the identity of the object."""
        return id(self.obj)

    def __eq__(self, other: object) -> bool:
        """Compare by the identity of the object."""
        return isinstance(other, DataRef) and other.obj is self.obj


def get_epochs(input: dict) -> mne.BaseEpochs:
    """Get the epochs of the ``EEG`` item of the data object.

    Parameters
    ----------
    input : dict
        The ``EEG`` item of the data object.

    Returns
    -------
    mne.BaseEpochs
        The epochs.

    Raises
    ------
    TypeError
        If the data is not epoched.

    """
    epochs = input["data"]
    if not isinstance(epochs, mne.BaseEpochs):
        raise_error(
            "The EEG markers need epoched data, got "
            f"{type(epochs).__name__}. Add an epoching preprocessor (e.g., "
            "EEGFixedLengthEpochs).",
            klass=TypeError,
        )
    return epochs


def get_picks(info: mne.Info, csd: bool = False) -> np.ndarray:
    """Get the indices of the data channels, excluding the bad ones.

    Parameters
    ----------
    info : mne.Info
        The measurement info.
    csd : bool, optional
        Whether to pick the current source density channels instead of the
        EEG and MEG ones (default False).

    Returns
    -------
    numpy.ndarray
        The indices of the channels.

    """
    if csd:
        return mne.pick_types(info, meg=False, csd=True, exclude="bads")
    return mne.pick_types(info, meg=True, eeg=True, exclude="bads")


def time_mask(
    times: np.ndarray,
    tmin: float | None = None,
    tmax: float | None = None,
    sfreq: float | None = None,
) -> np.ndarray:
    """Get the mask of the samples in a time interval (as in MNE).

    Parameters
    ----------
    times : numpy.ndarray
        The times of the samples.
    tmin : float or None, optional
        The start of the interval. If None, the first sample (default None).
    tmax : float or None, optional
        The end of the interval, included. If None, the last sample
        (default None).
    sfreq : float or None, optional
        The sampling frequency. If given, the interval is pushed to the
        nearest sample boundaries (default None).

    Returns
    -------
    numpy.ndarray
        The mask of the samples.

    """
    tmin = times[0] if tmin is None else tmin
    tmax = times[-1] if tmax is None else tmax
    if sfreq is not None:
        sfreq = float(sfreq)
        tmin = round(tmin * sfreq) / sfreq - 0.5 / sfreq
        tmax = round(tmax * sfreq) / sfreq + 0.5 / sfreq
    if tmin > tmax:
        raise_error(f"tmin ({tmin}) must be less than or equal to tmax")
    mask = (times >= tmin) & (times <= tmax)
    if not mask.any():
        raise_error(
            f"No samples between {tmin} and {tmax} (the data is between "
            f"{times[0]} and {times[-1]})"
        )
    return mask


def lowpass_epochs(
    data: np.ndarray, sfreq: float, filter_freq: float
) -> np.ndarray:
    """Low-pass filter epoched data (as in NICE).

    The epochs are concatenated, filtered with a zero-phase 6th order
    Butterworth filter and split again.

    Parameters
    ----------
    data : numpy.ndarray
        The data, shape (n_epochs, n_channels, n_times).
    sfreq : float
        The sampling frequency.
    filter_freq : float
        The cut-off frequency.

    Returns
    -------
    numpy.ndarray
        The filtered data, shape (n_epochs, n_channels, n_times).

    """
    n_epochs, n_channels, n_times = data.shape
    b, a = butter(6, 2.0 * filter_freq / sfreq, "lowpass")
    concatenated = np.hstack(data)
    filtered = filtfilt(b, a, concatenated)
    return filtered.reshape(n_channels, n_epochs, n_times).transpose(1, 0, 2)
