"""Provide class for resampling EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGResample"]


@register_preprocessor
class EEGResample(EEGBasePreprocessor):
    """Class for resampling EEG data.

    The data already at the sampling frequency is not changed.

    Parameters
    ----------
    sfreq : float
        The new sampling frequency, in Hz.

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    sfreq: float

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        if inst.info["sfreq"] == self.sfreq:
            return inst
        return inst.resample(self.sfreq, verbose="error")
