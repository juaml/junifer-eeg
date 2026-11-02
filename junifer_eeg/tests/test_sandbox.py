"""Provide tests for autoreject and the PLV, wPLI and ratio markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import mne
import numpy as np
import pytest
from mne_connectivity import spectral_connectivity_epochs

from junifer_eeg.conftest import make_epochs
from junifer_eeg.markers import (
    EEGPhaseLockingValueScalar,
    EEGPhaseLockingValueTopography,
    EEGPowerSpectralDensityScalar,
    EEGRatioScalar,
    EEGRatioTimeseries,
    EEGWeightedPhaseLagIndexScalar,
)
from junifer_eeg.preprocess import EEGAutoReject


_ESTIMATOR = {
    "method": "welch",
    "tmin": None,
    "tmax": 0.6,
    "fmin": 1.0,
    "fmax": 45.0,
    "method_params": {"n_fft": 4096, "n_overlap": 100, "nperseg": 128},
}
_MEAN = {"method": "mean"}


def _input(epochs: Any) -> dict[str, Any]:
    """Get the data object item for the epochs."""
    return {"data": epochs, "montage": "easycap-M1", "meta": {}}


def test_autoreject() -> None:
    """Test repairing and rejecting the epochs with autoreject."""
    epochs = make_epochs(n_epochs=40)
    data = epochs.get_data()
    # Noise of 30 µV (the data has ~6 µV peak-to-peak): in a channel of an
    # epoch (repaired) and in all the channels of another (dropped)
    rng = np.random.default_rng(0)
    data[3, 2] += 30e-6 * rng.standard_normal(data.shape[-1])
    data[7] += 30e-6 * rng.standard_normal(data.shape[1:])
    epochs = mne.EpochsArray(data, epochs.info, tmin=-0.2, verbose="error")
    params = {
        "n_interpolate": [1, 4],
        "consensus": [0.5],
        "cv": 4,
        "thresh_method": "random_search",
        "seed": 42,
    }
    out = EEGAutoReject(**params).preprocess(_input(epochs.copy()))["data"]
    assert len(out) == len(epochs) - 1
    assert out.drop_log[7] == ("AUTOREJECT",)
    # The repaired channel is within the range of the others
    assert np.ptp(out.get_data()[3, 2]) < 20e-6
    # Too few epochs remain
    with pytest.raises(RuntimeError, match="epochs remain"):
        EEGAutoReject(**params, min_epochs=1.0).preprocess(
            _input(epochs.copy())
        )


@pytest.mark.parametrize(
    "klass, method",
    [
        (EEGPhaseLockingValueScalar, "plv"),
        (EEGWeightedPhaseLagIndexScalar, "wpli"),
    ],
)
def test_spectral_connectivity(klass: type, method: str) -> None:
    """Test the PLV and wPLI against mne-connectivity."""
    epochs = make_epochs()
    bands = {"theta": [4.0, 8.0], "alpha": [8.0, 12.0]}
    marker = klass(
        tmax=0.6,
        bands=bands,
        aggregations={
            "mean": [
                {"axis": "channels_y", **_MEAN},
                {"axis": "channels", **_MEAN},
            ]
        },
    )
    values, features, ch_names = marker.compute_values(_input(epochs))
    assert features == ["theta", "alpha"]
    assert ch_names == epochs.ch_names
    n_channels = len(ch_names)
    assert values.shape == (n_channels, n_channels, 2)
    np.testing.assert_allclose(values, values.transpose(1, 0, 2))
    np.testing.assert_array_equal(values[np.diag_indices(n_channels)], 0)
    con = spectral_connectivity_epochs(
        epochs.copy().crop(None, 0.6),
        method=method,
        fmin=(4.0, 8.0),
        fmax=(8.0, 12.0),
        faverage=True,
        verbose="error",
    )
    expected = con.get_data("dense")
    np.testing.assert_allclose(values, expected + expected.transpose(1, 0, 2))
    out = marker.compute(_input(epochs))["mean"]
    np.testing.assert_allclose(out["data"], values.mean(axis=(0, 1)))


def test_spectral_connectivity_validation() -> None:
    """Test the validation of the PLV parameters."""
    agg = {"mean": [{"axis": "channels_y", **_MEAN}]}
    # The topographies keep the channels; there are no epochs
    EEGPhaseLockingValueTopography(bands={"a": [8.0, 12.0]}, aggregations=agg)
    with pytest.raises(ValueError, match="channels_y"):
        EEGPhaseLockingValueTopography(
            bands={"a": [8.0, 12.0]},
            aggregations={"mean": [{"axis": "epochs", **_MEAN}]},
        )
    with pytest.raises(ValueError, match="fmin < fmax"):
        EEGPhaseLockingValueTopography(
            bands={"a": [12.0, 8.0]}, aggregations=agg
        )


def test_ratio() -> None:
    """Test the ratio of the theta and alpha power."""
    epochs = make_epochs()
    psd_params = {
        "estimator": _ESTIMATOR,
        "bands": {"theta": [4.0, 8.0], "alpha": [8.0, 12.0]},
        "dB": False,
        "normalized": False,
    }
    ratio = {
        "name": "theta_alpha",
        "numerator": {
            "marker": "EEGPowerSpectralDensity",
            "feature": "theta",
            "params": psd_params,
        },
        "denominator": {
            "marker": "EEGPowerSpectralDensity",
            "feature": "alpha",
            "params": psd_params,
        },
    }
    marker = EEGRatioTimeseries(
        ratios=[ratio],
        aggregations={
            "mean": [{"axis": "channels", "picks": "scalp", **_MEAN}]
        },
    )
    values, features, _ = marker.compute_values(_input(epochs))
    assert features == ["theta_alpha"]
    psd = EEGPowerSpectralDensityScalar(
        **psd_params,
        aggregations={
            "mean": [
                {"axis": "epochs", **_MEAN},
                {"axis": "channels", **_MEAN},
            ]
        },
    )
    power, _, _ = psd.compute_values(_input(epochs))
    np.testing.assert_allclose(values[..., 0], power[..., 0] / power[..., 1])
    out = marker.compute(_input(epochs))["mean"]
    assert out["data"].shape == (len(epochs), 1)

    # Scalars, epochs first
    out = EEGRatioScalar(
        ratios=[ratio],
        aggregations={
            "mean": [
                {"axis": "epochs", **_MEAN},
                {"axis": "channels", **_MEAN},
            ]
        },
    ).compute(_input(epochs))["mean"]
    np.testing.assert_allclose(out["data"], values.mean(axis=(0, 1)))


def test_ratio_validation() -> None:
    """Test the validation of the ratio operands."""
    agg = {
        "mean": [{"axis": "epochs", **_MEAN}, {"axis": "channels", **_MEAN}]
    }

    def _ratio(marker: str, feature: str = "x", **params: Any) -> dict:
        operand = {"marker": marker, "feature": feature, "params": params}
        return {"name": "r", "numerator": operand, "denominator": operand}

    # A kind, not a base marker
    with pytest.raises(ValueError, match="base class"):
        EEGRatioScalar(
            ratios=[_ratio("EEGPowerSpectralDensityScalar")],
            aggregations=agg,
        )
    # Other axes
    with pytest.raises(ValueError, match="axes"):
        EEGRatioScalar(
            ratios=[_ratio("EEGSymbolicMutualInformation")], aggregations=agg
        )
    # Invalid parameters of the marker
    with pytest.raises(ValueError):
        EEGRatioScalar(
            ratios=[_ratio("EEGPermutationEntropy", kernel="x")],
            aggregations=agg,
        )
    # Unknown feature
    marker = EEGRatioScalar(
        ratios=[_ratio("EEGPermutationEntropy", tmax=0.6)], aggregations=agg
    )
    with pytest.raises(ValueError, match="no feature x"):
        marker.compute_values(_input(make_epochs()))
