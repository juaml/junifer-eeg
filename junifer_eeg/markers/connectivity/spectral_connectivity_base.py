"""Provide base class for the spectral connectivity markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from typing import Any, ClassVar, Literal

import numpy as np
from junifer.typing import Dependencies
from junifer.utils import raise_error
from mne_connectivity import spectral_connectivity_epochs

from ..aggregation import Axis
from ..base import EEGBaseMarker
from ..utils import get_epochs, get_picks, time_mask


__all__ = ["EEGSpectralConnectivity"]


class EEGSpectralConnectivity(EEGBaseMarker):
    """Base class for the spectral connectivity markers.

    The connectivity of each pair of channels is estimated across the epochs
    with :func:`mne_connectivity.spectral_connectivity_epochs` (method set by
    the concrete class), averaged over the frequencies of each band (a
    feature). The values of a channel with itself are 0. As the epochs are
    used to estimate the connectivity, there is no ``epochs`` axis (and no
    timeseries kind).

    Parameters
    ----------
    tmin : float or None, optional
        The start of the epochs to use. If None, from the start
        (default None).
    tmax : float or None, optional
        The end of the epochs to use. If None, until the end (default None).
    bands : dict of str and list of float
        The name and the ``[fmin, fmax]`` of each frequency band.
    mode : {"multitaper", "fourier"}, optional
        The spectrum estimation mode (default "multitaper").
    method_params : dict or None, optional
        Other parameters of the spectrum estimation, e.g., ``mt_bandwidth``
        (default None).
    n_jobs : int, optional
        The number of parallel jobs (default 1).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {
        "mne",
        "mne-connectivity",
        "numpy",
        "junifer_eeg",
    }
    _AXES: ClassVar[tuple[Axis, ...]] = ("channels", "channels_y")
    # The connectivity method of mne_connectivity, set by the concrete class
    _METHOD: ClassVar[str]

    tmin: float | None = None
    tmax: float | None = None
    bands: dict[str, list[float]]
    mode: Literal["multitaper", "fourier"] = "multitaper"
    method_params: dict[str, Any] | None = None
    n_jobs: int = 1

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        if len(self.bands) == 0:
            raise_error("At least one band is needed")
        for name, band in self.bands.items():
            if len(band) != 2 or band[0] >= band[1]:
                raise_error(f"Band {name} must be [fmin, fmax], fmin < fmax")

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the connectivity in each band.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray
            The values, shape (n_channels, n_channels, n_bands).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        epochs = get_epochs(input)
        picks = get_picks(epochs.info)
        sfreq = epochs.info["sfreq"]
        mask = time_mask(epochs.times, self.tmin, self.tmax, sfreq=sfreq)
        data = epochs.get_data(picks=picks)[..., mask]
        fmin, fmax = zip(*self.bands.values(), strict=True)
        con = spectral_connectivity_epochs(
            data,
            method=self._METHOD,
            sfreq=sfreq,
            mode=self.mode,
            fmin=fmin,
            fmax=fmax,
            faverage=True,
            n_jobs=self.n_jobs,
            verbose="error",
            **(self.method_params or {}),
        )
        # The lower triangle, made symmetric
        values = con.get_data("dense")
        values = values + values.transpose(1, 0, 2)
        ch_names = [epochs.ch_names[x] for x in picks]
        return values, list(self.bands), ch_names
