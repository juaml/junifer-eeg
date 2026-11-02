"""Provide class for the parameters of the PSD estimation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


__all__ = ["PSDEstimatorParams"]


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
