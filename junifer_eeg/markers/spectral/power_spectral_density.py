"""Provide the power spectral density (PSD) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar

import numpy as np
from junifer.api.decorators import register_marker
from junifer.typing import Dependencies
from junifer.utils import raise_error

from ..aggregation import entropy
from ..base import EEGBaseMarker, ScalarMixin, TimeseriesMixin, TopographyMixin
from ..utils import get_epochs
from ._psd_estimator import PSDEstimator, PSDEstimatorParams


__all__ = [
    "EEGPowerSpectralDensity",
    "EEGPowerSpectralDensityScalar",
    "EEGPowerSpectralDensityTimeseries",
    "EEGPowerSpectralDensityTopography",
]


class EEGPowerSpectralDensity(EEGBaseMarker):
    """Base class for the spectral markers.

    The features are computed from the PSD (see :class:`PSDEstimator`),
    reducing the frequency axis:

    * ``<band>``: the sum of the PSD in each band, in dB if ``dB``.
    * ``<band>n``: the sum of the normalized PSD (divided by the total power
      of the estimator frequencies) in each band, if ``normalized``.
    * ``se``: the spectral entropy of the normalized PSD, if
      ``spectral_entropy``.
    * ``<edge>``: the frequency below which each fraction of the power lies
      (e.g., the median spectral frequency for 0.5), for each of the
      ``spectral_edges``.

    Parameters
    ----------
    estimator : PSDEstimatorParams
        The parameters of the PSD estimation.
    bands : dict of str and list of float or None, optional
        The frequency bands, as the name and the minimum and maximum
        frequencies (both included) (default None).
    dB : bool, optional
        Whether to compute the power in the bands in dB (default True).
    normalized : bool, optional
        Whether to also compute the normalized power in the bands
        (default False).
    spectral_entropy : bool, optional
        Whether to compute the spectral entropy (default False).
    spectral_edges : dict of str and float or None, optional
        The spectral edges to compute, as the name and the fraction of the
        power (default None).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {
        "mne",
        "numpy",
        "scipy",
        "junifer_eeg",
    }

    estimator: PSDEstimatorParams
    bands: dict[str, tuple[float, float]] | None = None
    dB: bool = True  # noqa: N815
    normalized: bool = False
    spectral_entropy: bool = False
    spectral_edges: dict[str, float] | None = None

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        if not (self.bands or self.spectral_entropy or self.spectral_edges):
            raise_error(
                "No spectral features: set `bands`, `spectral_entropy` or "
                "`spectral_edges`"
            )
        for band, (fmin, fmax) in (self.bands or {}).items():
            if fmin > fmax:
                raise_error(f"Band {band}: fmin ({fmin}) > fmax ({fmax})")
            if fmin < self.estimator.fmin or (
                self.estimator.fmax is not None and fmax > self.estimator.fmax
            ):
                raise_error(
                    f"Band {band} ({fmin}-{fmax} Hz) not in the frequencies "
                    "of the estimator"
                )
        for edge, fraction in (self.spectral_edges or {}).items():
            if not 0 < fraction < 1:
                raise_error(
                    f"Spectral edge {edge} must be between 0 and 1, got "
                    f"{fraction}"
                )

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the spectral features.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray
            The values, shape (n_epochs, n_channels, n_features).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        epochs = get_epochs(input)
        psds, freqs, ch_names = PSDEstimator().compute(epochs, self.estimator)
        psds_norm = psds / psds.sum(axis=-1, keepdims=True)
        values = []
        features = []
        for band, (fmin, fmax) in (self.bands or {}).items():
            start = np.searchsorted(freqs, fmin, "left")
            end = np.searchsorted(freqs, fmax, "right")
            power = psds[..., start:end].sum(axis=-1)
            if self.dB:
                power = 10 * np.log10(power)
            values.append(power)
            features.append(band)
            if self.normalized:
                values.append(psds_norm[..., start:end].sum(axis=-1))
                features.append(f"{band}n")
        if self.spectral_entropy:
            values.append(entropy(psds_norm, axis=-1))
            features.append("se")
        if self.spectral_edges:
            cumulative = np.cumsum(psds_norm, axis=-1)
            for edge, fraction in self.spectral_edges.items():
                idx = np.argmin((cumulative - fraction) ** 2, axis=-1)
                values.append(freqs[idx])
                features.append(edge)
        return np.stack(values, axis=-1), features, ch_names


@register_marker
class EEGPowerSpectralDensityScalar(ScalarMixin, EEGPowerSpectralDensity):
    """Class for the spectral markers, reduced to scalars.

    See :class:`.EEGPowerSpectralDensity` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGPowerSpectralDensityTopography(
    TopographyMixin, EEGPowerSpectralDensity
):
    """Class for the spectral markers, reduced to topographies.

    See :class:`.EEGPowerSpectralDensity` and :class:`.TopographyMixin`.

    """


@register_marker
class EEGPowerSpectralDensityTimeseries(
    TimeseriesMixin, EEGPowerSpectralDensity
):
    """Class for the spectral markers, reduced to one value per epoch.

    See :class:`.EEGPowerSpectralDensity` and :class:`.TimeseriesMixin`.

    """
