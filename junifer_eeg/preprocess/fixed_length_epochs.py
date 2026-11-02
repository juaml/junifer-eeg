"""Provide class for cutting continuous EEG data into pseudo-epochs."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
import numpy as np
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error

from .base import EEGBasePreprocessor


__all__ = ["EEGFixedLengthEpochs"]


@register_preprocessor
class EEGFixedLengthEpochs(EEGBasePreprocessor):
    """Class for cutting continuous EEG data into pseudo-epochs.

    Fixed-length epochs are cut every ``duration`` plus a random ``jitter``,
    starting at ``onset``. Each epoch spans from ``tmin`` to
    ``tmin + duration`` around its event (both included).

    Parameters
    ----------
    duration : float
        The length of each epoch, in seconds.
    tmin : float, optional
        The start of each epoch relative to its event, in seconds
        (default 0.0).
    onset : float, optional
        The time of the first event, in seconds (default 0.0).
    jitter : list of float or None, optional
        The minimum and maximum time between the end of an epoch and the next
        event, in seconds. The time is drawn uniformly (in samples) for each
        epoch. If None, the epochs are contiguous (default None).
    baseline : list of float or None, optional
        The baseline interval. See :class:`mne.Epochs` (default None).
    seed : int, optional
        The seed of the random number generator for the jitter, so the epochs
        are the same every time (default 0).

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    duration: float
    tmin: float = 0.0
    onset: float = 0.0
    jitter: list[float] | None = None
    baseline: list[float | None] | None = None
    seed: int = 0

    def validate_preprocessor_params(self) -> None:
        """Run extra logical validation for the preprocessor."""
        if self.jitter is not None and (
            len(self.jitter) != 2 or self.jitter[0] > self.jitter[1]
        ):
            raise_error("`jitter` must be a list of [minimum, maximum]")

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        sfreq = inst.info["sfreq"]
        epoch_len = int(np.ceil(self.duration * sfreq))
        onset = int(np.ceil(self.onset * sfreq))
        if self.jitter is None:
            min_jitter = max_jitter = 0
        else:
            min_jitter = int(np.ceil(self.jitter[0] * sfreq))
            max_jitter = int(np.ceil(self.jitter[1] * sfreq))
        rng = np.random.default_rng(self.seed)
        # Draw enough jitters for the longest sequence of events
        max_events = int(np.ceil(len(inst.times) / epoch_len)) + 1
        jitters = rng.integers(
            min_jitter, max_jitter, size=max_events, endpoint=True
        )
        samples = []
        this_sample = onset
        for this_jitter in jitters:
            if this_sample >= len(inst.times):
                break
            samples.append(this_sample)
            this_sample += epoch_len + this_jitter
        samples = np.array(samples, dtype=int) + inst.first_samp
        events = np.c_[
            samples,
            np.zeros(len(samples), dtype=int),
            np.ones(len(samples), dtype=int),
        ]
        baseline = None if self.baseline is None else tuple(self.baseline)
        return mne.Epochs(
            inst,
            events,
            event_id=1,
            tmin=self.tmin,
            tmax=self.tmin + self.duration,
            baseline=baseline,
            reject=None,
            preload=True,
            verbose="error",
        )
