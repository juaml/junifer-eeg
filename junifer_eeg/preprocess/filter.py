"""Provide class for filtering EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGFilter"]


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
