"""Provide preprocessors for filtering and resampling the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGFilter", "EEGNotchFilter", "EEGResample"]


@register_preprocessor
class EEGFilter(EEGBasePreprocessor):
    """Class for filtering EEG data.

    Parameters
    ----------
    l_freq : float or None
        The low cut-off frequency in Hz. If None, the data is low-passed.
    h_freq : float or None
        The high cut-off frequency in Hz. If None, the data is high-passed.
    method : {"fir", "iir"}, optional
        The filter method (default "fir").
    iir_params : dict or None, optional
        The parameters of the IIR filter, e.g., ``ftype`` and ``order``.
        See :func:`mne.filter.construct_iir_filter` (default None).
    phase : str, optional
        The phase of the filter. See :meth:`mne.io.Raw.filter`
        (default "zero").

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    l_freq: float | None
    h_freq: float | None
    method: str = "fir"
    iir_params: dict[str, Any] | None = None
    phase: str = "zero"

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        return inst.filter(
            l_freq=self.l_freq,
            h_freq=self.h_freq,
            method=self.method,
            iir_params=self.iir_params,
            phase=self.phase,
            verbose="error",
        )


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
