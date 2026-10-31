"""Provide preprocessors for rejecting bad EEG channels and epochs."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import math
from typing import Any, ClassVar

import mne
import numpy as np
import structlog
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error
from scipy.signal import butter, filtfilt
from scipy.stats import zscore

from .base import EEGBasePreprocessor


__all__ = ["EEGAdaptiveRejection"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="preprocess", step="preprocessing")


@register_preprocessor
class EEGAdaptiveRejection(EEGBasePreprocessor):
    """Class for the adaptive rejection of bad EEG channels and epochs.

    Port of ``_adaptive_egi`` from nice-extensions. In order:

    1. Bad channels by threshold: the channels whose peak-to-peak amplitude
       exceeds ``reject`` in more than ``n_epochs_bad_ch`` epochs.
    2. Bad channels by variance: the channels whose variance is an outlier
       (iterated z-scoring with ``zscore_thresh`` and ``max_iter``).
    3. Bad epochs by threshold: the epochs in which more than
       ``n_channels_bad_epoch`` of the good channels exceed ``reject``. They
       are dropped.
    4. Bad channels by high frequency: the channels whose standard deviation
       above 25 Hz is an outlier.

    The bad channels are marked as bad (``info["bads"]``). Then, the subject
    is rejected (an error is raised) if fewer than ``min_channels`` channels
    are good or fewer than ``min_epochs`` epochs remain.

    Parameters
    ----------
    reject : dict
        The peak-to-peak amplitude threshold for each channel type, e.g.,
        ``{"eeg": 100e-6}``.
    n_epochs_bad_ch : float or int, optional
        The number (int) or proportion (float) of epochs exceeding the
        threshold for a channel to be bad (default 0.5).
    n_channels_bad_epoch : float or int, optional
        The number (int) or proportion (float) of good channels exceeding the
        threshold for an epoch to be bad (default 0.1).
    zscore_thresh : float, optional
        The z-score threshold for the outlier detection (default 4).
    max_iter : int, optional
        The maximum number of iterations of the outlier detection
        (default 4).
    min_channels : float or int or None, optional
        The minimum number (int) or proportion (float) of good channels. If
        None, it is not checked (default None).
    min_epochs : float or int or None, optional
        The minimum number (int) or proportion (float) of epochs remaining,
        out of the epochs before rejection. If None, it is not checked
        (default None).

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.BaseEpochs,)

    reject: dict[str, float]
    n_epochs_bad_ch: float | int = 0.5
    n_channels_bad_epoch: float | int = 0.1
    zscore_thresh: float = 4
    max_iter: int = 4
    min_channels: float | int | None = None
    min_epochs: float | int | None = None

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        bad_channels = set()
        picks = mne.pick_types(inst.info, eeg=True, exclude="bads")

        bad_chs = _find_bad_channels_threshold(
            inst, picks, self.reject, self.n_epochs_bad_ch
        )
        logger.info(f"Bad channels by threshold: {bad_chs}")
        bad_channels.update(bad_chs)

        picks = _picks_excluding(inst, bad_channels)
        bad_chs = _find_bad_channels_variance(
            inst, picks, self.zscore_thresh, self.max_iter
        )
        logger.info(f"Bad channels by variance: {bad_chs}")
        bad_channels.update(bad_chs)

        picks = _picks_excluding(inst, bad_channels)
        bad_epochs = _find_bad_epochs_threshold(
            inst, picks, self.reject, self.n_channels_bad_epoch
        )
        logger.info(f"Bad epochs by threshold: {len(bad_epochs)}")
        n_epochs = len(inst)
        inst.drop(bad_epochs, reason="artifacted", verbose="error")

        picks = _picks_excluding(inst, bad_channels)
        bad_chs = _find_bad_channels_high_frequency(
            inst, picks, self.zscore_thresh, self.max_iter
        )
        logger.info(f"Bad channels by high frequency: {bad_chs}")
        bad_channels.update(bad_chs)

        bad_channels = sorted(bad_channels)
        logger.info(f"Bad channels: {len(bad_channels)} {bad_channels}")
        inst.info["bads"].extend(
            [x for x in bad_channels if x not in inst.info["bads"]]
        )
        self._check_min_channels(inst)
        self._check_min_epochs(inst, n_epochs)
        return inst

    def _check_min_channels(self, inst: mne.BaseEpochs) -> None:
        """Check the number of good channels."""
        if self.min_channels is None:
            return
        n_channels = len(mne.pick_types(inst.info, eeg=True, exclude=[]))
        min_channels = self.min_channels
        if isinstance(min_channels, float):
            min_channels = int(n_channels * min_channels)
        n_good = n_channels - len(inst.info["bads"])
        if n_good < min_channels:
            raise_error(
                f"Cannot clean data: only {n_good} out of {n_channels} "
                f"channels are good (minimum {min_channels}).",
                klass=RuntimeError,
            )

    def _check_min_epochs(self, inst: mne.BaseEpochs, n_epochs: int) -> None:
        """Check the number of epochs remaining."""
        if self.min_epochs is None:
            return
        min_epochs = self.min_epochs
        if isinstance(min_epochs, float):
            min_epochs = int(n_epochs * min_epochs)
        if len(inst) < min_epochs:
            raise_error(
                f"Cannot clean data: only {len(inst)} out of {n_epochs} "
                f"epochs remain (minimum {min_epochs}).",
                klass=RuntimeError,
            )


def _picks_excluding(inst: mne.BaseEpochs, exclude: set[str]) -> np.ndarray:
    """Get the indices of the channels, excluding some of them."""
    return mne.pick_channels(inst.ch_names, include=[], exclude=list(exclude))


def _n_from_proportion(value: float | int, total: int) -> int:
    """Get a number from a number (int) or a proportion (float)."""
    if isinstance(value, float):
        return math.floor(value * total)
    return value


def _find_outliers(
    values: np.ndarray, threshold: float, max_iter: int
) -> np.ndarray:
    """Find outliers with iterated z-scoring (as in MNE).

    Parameters
    ----------
    values : numpy.ndarray
        The values, shape (n_values,).
    threshold : float
        The absolute z-score above which a value is an outlier.
    max_iter : int
        The maximum number of iterations.

    Returns
    -------
    numpy.ndarray
        The indices of the outliers.

    """
    mask = np.zeros(len(values), dtype=bool)
    for _ in range(max_iter):
        masked = np.ma.masked_array(values, mask)
        local_bad = np.abs(zscore(masked)) > threshold
        mask = np.max([mask, local_bad], 0)
        if not np.any(local_bad):
            break
    return np.where(mask)[0]


def _find_bad_channels_threshold(
    inst: mne.BaseEpochs,
    picks: np.ndarray,
    reject: dict[str, float],
    n_epochs_bad_ch: float | int,
) -> list[str]:
    """Find the channels exceeding the threshold in too many epochs."""
    data = inst.get_data()
    n_epochs_bad_ch = _n_from_proportion(n_epochs_bad_ch, data.shape[0])
    ch_types = np.array(inst.get_channel_types())
    bad_chs = []
    for ch_type, thresh in reject.items():
        idx = np.array([x for x in picks if ch_types[x] == ch_type], int)
        ptp = np.ptp(data[:, idx], axis=-1)
        count = (ptp > thresh).sum(axis=0)
        bad_chs.extend(inst.ch_names[x] for x in idx[count > n_epochs_bad_ch])
    return bad_chs


def _find_bad_channels_variance(
    inst: mne.BaseEpochs,
    picks: np.ndarray,
    zscore_thresh: float,
    max_iter: int,
) -> list[str]:
    """Find the channels with outlier variance."""
    data = np.hstack(inst.get_data()[:, picks])
    bad = _find_outliers(data.var(axis=-1), zscore_thresh, max_iter)
    return [inst.ch_names[picks[x]] for x in bad]


def _find_bad_epochs_threshold(
    inst: mne.BaseEpochs,
    picks: np.ndarray,
    reject: dict[str, float],
    n_channels_bad_epoch: float | int,
) -> np.ndarray:
    """Find the epochs in which too many channels exceed the threshold."""
    n_channels_bad_epoch = _n_from_proportion(n_channels_bad_epoch, len(picks))
    data = inst.get_data()
    ch_types = np.array(inst.get_channel_types())
    bad_epochs = []
    for ch_type, thresh in reject.items():
        idx = np.array([x for x in picks if ch_type == ch_types[x]], int)
        ptp = np.ptp(data[:, idx], axis=-1)
        count = (ptp > thresh).sum(axis=1)
        bad_epochs.append(np.where(count > n_channels_bad_epoch)[0])
    return np.unique(np.concatenate(bad_epochs))


def _find_bad_channels_high_frequency(
    inst: mne.BaseEpochs,
    picks: np.ndarray,
    zscore_thresh: float,
    max_iter: int,
) -> list[str]:
    """Find the channels with outlier standard deviation above 25 Hz."""
    data = np.hstack(inst.get_data()[:, picks])
    b, a = butter(4, 2.0 * 25 / inst.info["sfreq"], "highpass")
    filt_data = filtfilt(b, a, data)
    bad = _find_outliers(filt_data.std(axis=-1), zscore_thresh, max_iter)
    return [inst.ch_names[picks[x]] for x in bad]
