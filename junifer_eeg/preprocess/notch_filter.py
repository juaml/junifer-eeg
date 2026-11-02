"""Provide class for notch filtering EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGNotchFilter"]


@register_preprocessor
class EEGNotchFilter(EEGBasePreprocessor):
    """Class for notch filtering EEG data.

    Parameters
    ----------
    freqs : list of float
        The frequencies to remove, in Hz (e.g., the line frequency and its
        harmonics).
    method : {"fir", "iir", "spectrum_fit"}, optional
        The filter method (default "fir").

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    freqs: list[float]
    method: str = "fir"

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        return inst.notch_filter(
            freqs=self.freqs, method=self.method, verbose="error"
        )
