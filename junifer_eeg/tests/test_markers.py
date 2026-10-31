"""Provide tests for the EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import numpy as np
import pytest
from junifer.storage import StorageType
from scipy.signal import welch
from scipy.stats import trim_mean

from junifer_eeg.conftest import make_epochs
from junifer_eeg.markers import (
    EEGKolmogorovComplexityScalar,
    EEGKolmogorovComplexityTopography,
    EEGPermutationEntropyScalar,
    EEGPermutationEntropyTimeseries,
    EEGPowerSpectralDensityScalar,
    EEGPowerSpectralDensityTimeseries,
    EEGPowerSpectralDensityTopography,
    EEGSymbolicMutualInformationScalar,
    EEGSymbolicMutualInformationTopography,
    PSDEstimator,
    SMIEstimator,
)
from junifer_eeg.markers.aggregation import entropy, get_aggregation_function
from junifer_eeg.markers.symbolic import symbolize
from junifer_eeg.markers.utils import time_mask
from junifer_eeg.tests import _nice_reference as nice


_ESTIMATOR = {
    "tmin": None,
    "tmax": 0.6,
    "fmin": 1.0,
    "fmax": 45.0,
    "method_params": {"n_fft": 4096, "n_overlap": 100, "nperseg": 128},
}
_MEAN_EPOCHS = {"axis": "epochs", "method": "mean"}
_SCALP_MEAN = {"axis": "channels", "method": "mean", "picks": "scalp"}


def _input(epochs: Any) -> dict[str, Any]:
    """Get the data object item for the epochs."""
    return {"data": epochs, "montage": "easycap-M1", "meta": {}}


@pytest.fixture
def epochs() -> Any:
    """Return synthetic epochs."""
    return make_epochs()


def test_symbolize_matches_nice() -> None:
    """Test the symbolic transformation against NICE."""
    rng = np.random.default_rng(0)
    data = rng.standard_normal((4, 100))
    for kernel, tau in [(3, 1), (3, 4), (4, 2)]:
        expected, _ = nice._symb_python(data, kernel, tau)
        np.testing.assert_array_equal(symbolize(data, kernel, tau), expected)


def test_entropy() -> None:
    """Test the normalized entropy."""
    uniform = np.full((2, 8), 1 / 8)
    np.testing.assert_allclose(entropy(uniform, axis=-1), [1.0, 1.0])
    peaked = np.zeros(8)
    peaked[3] = 1
    assert entropy(peaked) == 0


def test_get_aggregation_function() -> None:
    """Test the aggregation functions."""
    data = np.arange(20.0).reshape(4, 5)
    func = get_aggregation_function("trim_mean", {"proportiontocut": 0.1})
    np.testing.assert_allclose(func(data, axis=0), trim_mean(data, 0.1))
    np.testing.assert_allclose(
        get_aggregation_function("sum")(data, axis=1), data.sum(1)
    )
    with pytest.raises(ValueError, match="Unknown aggregation"):
        get_aggregation_function("foo")
    with pytest.raises(ValueError, match="takes no parameters"):
        get_aggregation_function("median", {"foo": 1})


def test_time_mask() -> None:
    """Test the time mask."""
    times = np.arange(201) / 250 - 0.2
    assert time_mask(times).all()
    assert time_mask(times, tmax=0.0).sum() == 51
    assert time_mask(times, tmin=0.0, sfreq=250).sum() == 151
    with pytest.raises(ValueError, match="No samples"):
        time_mask(times, tmin=1.0, tmax=2.0)


def test_psd_scalar(epochs: Any) -> None:
    """Test the spectral markers against a direct computation."""
    marker = EEGPowerSpectralDensityScalar(
        estimator=_ESTIMATOR,
        bands={"alpha": [8.0, 12.0], "beta": [12.0, 30.0]},
        dB=True,
        normalized=True,
        spectral_entropy=True,
        spectral_edges={"msf": 0.5},
        aggregations={"mean": [_SCALP_MEAN, _MEAN_EPOCHS]},
    )
    out = marker.compute(_input(epochs))
    assert list(out) == ["mean"]
    assert out["mean"]["col_names"] == [
        "alpha",
        "alphan",
        "beta",
        "betan",
        "se",
        "msf",
    ]
    # Direct computation, the whole epoch (tmax=0.6) on the scalp
    data = epochs.get_data()
    freqs, psds = welch(
        data,
        fs=250.0,
        window="hamming",
        nperseg=128,
        noverlap=100,
        nfft=4096,
    )
    mask = (freqs >= 1.0) & (freqs <= 45.0)
    freqs, psds = freqs[mask], psds[..., mask]
    norm = psds / psds.sum(-1, keepdims=True)
    alpha = (freqs >= 8.0) & (freqs <= 12.0)
    scalp = slice(0, 17)
    expected_alpha = (10 * np.log10(psds[..., alpha].sum(-1)))[:, scalp]
    expected_alphan = norm[..., alpha].sum(-1)[:, scalp]
    np.testing.assert_allclose(
        out["mean"]["data"][0], expected_alpha.mean(1).mean(0)
    )
    np.testing.assert_allclose(
        out["mean"]["data"][1], expected_alphan.mean(1).mean(0)
    )
    # The alpha oscillation dominates the spectrum
    assert out["mean"]["data"][1] > out["mean"]["data"][3]
    assert 8 < out["mean"]["data"][5] < 12
    assert marker.storage_type("EEG", "mean") == StorageType.Vector


def test_psd_cache(epochs: Any) -> None:
    """Test that the PSD is computed once for the same data."""
    estimator = PSDEstimator()
    estimator._compute.cache_clear()
    kwargs = {
        "estimator": _ESTIMATOR,
        "bands": {"alpha": [8.0, 12.0]},
    }
    EEGPowerSpectralDensityScalar(
        **kwargs, aggregations={"mean": [_SCALP_MEAN, _MEAN_EPOCHS]}
    ).compute(_input(epochs))
    EEGPowerSpectralDensityTopography(
        **kwargs, aggregations={"mean": [_MEAN_EPOCHS]}
    ).compute(_input(epochs))
    info = estimator._compute.cache_info()
    assert info.misses == 1
    assert info.hits == 1


def test_psd_topography_and_timeseries(epochs: Any) -> None:
    """Test the dimensionality of the outputs."""
    kwargs = {"estimator": _ESTIMATOR, "bands": {"alpha": [8.0, 12.0]}}
    topo = EEGPowerSpectralDensityTopography(
        **kwargs, aggregations={"mean": [_MEAN_EPOCHS]}
    ).compute(_input(epochs))["mean"]
    assert topo["data"].shape == (20, 1)
    assert topo["row_names"] == epochs.ch_names
    assert topo["row_header_col_name"] == "channel"
    ts = EEGPowerSpectralDensityTimeseries(
        **kwargs, aggregations={"mean": [_SCALP_MEAN]}
    ).compute(_input(epochs))["mean"]
    assert ts["data"].shape == (len(epochs), 1)


@pytest.mark.parametrize(
    "aggregations, match",
    [
        ({}, "At least one"),
        ({"a": [_MEAN_EPOCHS]}, "missing: \\['channels'\\]"),
        ({"a": [_SCALP_MEAN, _MEAN_EPOCHS, _MEAN_EPOCHS]}, "repeated"),
        (
            {
                "a": [
                    _SCALP_MEAN,
                    _MEAN_EPOCHS,
                    {"axis": "channels_y", "method": "mean"},
                ]
            },
            "not allowed",
        ),
        (
            {"a": [_SCALP_MEAN, {"axis": "epochs", "method": "foo"}]},
            "Unknown aggregation",
        ),
    ],
)
def test_aggregation_validation(aggregations: dict, match: str) -> None:
    """Test the validation of the aggregations."""
    with pytest.raises(ValueError, match=match):
        EEGPermutationEntropyScalar(aggregations=aggregations)


def test_bands_validation() -> None:
    """Test the validation of the spectral features."""
    agg = {"mean": [_SCALP_MEAN, _MEAN_EPOCHS]}
    with pytest.raises(ValueError, match="not in the frequencies"):
        EEGPowerSpectralDensityScalar(
            estimator=_ESTIMATOR, bands={"x": [40.0, 60.0]}, aggregations=agg
        )
    with pytest.raises(ValueError, match="No spectral features"):
        EEGPowerSpectralDensityScalar(estimator=_ESTIMATOR, aggregations=agg)


def test_pe_matches_nice(epochs: Any) -> None:
    """Test the PE against NICE."""
    marker = EEGPermutationEntropyTimeseries(
        kernel=3,
        tau=4,
        aggregations={"all": [{"axis": "channels", "method": "mean"}]},
    )
    values, features, ch_names = marker.compute_values(_input(epochs))
    assert features == ["pe"]
    assert ch_names == epochs.ch_names
    expected = nice.pe(epochs.get_data(), 250.0, 3, 4)
    np.testing.assert_allclose(values[..., 0], expected.T)
    out = marker.compute(_input(epochs))["all"]
    np.testing.assert_allclose(out["data"][:, 0], expected.mean(0))


def test_kc_matches_nice(epochs: Any) -> None:
    """Test the KC against NICE."""
    marker = EEGKolmogorovComplexityTopography(
        nbins=32, aggregations={"mean": [_MEAN_EPOCHS]}
    )
    values, features, _ = marker.compute_values(_input(epochs))
    assert features == ["kc"]
    expected = nice.komplexity(epochs.get_data(), 32)
    np.testing.assert_allclose(values[..., 0], expected.T)


@pytest.mark.parametrize("method", ["weighted", "smi"])
def test_wsmi_matches_nice(method: str) -> None:
    """Test the wSMI against NICE (without CSD)."""
    epochs = make_epochs(n_epochs=3)
    marker = EEGSymbolicMutualInformationTopography(
        kernel=3,
        tau=4,
        method=method,
        csd=False,
        aggregations={
            "median": [
                {"axis": "channels_y", "method": "median"},
                _MEAN_EPOCHS,
            ]
        },
    )
    values, _, _ = marker.compute_values(_input(epochs))
    expected_wsmi, expected_smi = nice.wsmi(epochs.get_data(), 250.0, 3, 4)
    expected = expected_wsmi if method == "weighted" else expected_smi
    np.testing.assert_allclose(
        values[..., 0], expected.transpose(2, 0, 1), atol=1e-12
    )
    out = marker.compute(_input(epochs))["median"]
    np.testing.assert_allclose(
        out["data"][:, 0], np.median(expected, axis=1).mean(-1), atol=1e-12
    )


def test_wsmi_csd_scalar(epochs: Any) -> None:
    """Test the wSMI with CSD, reduced to a scalar."""
    marker = EEGSymbolicMutualInformationScalar(
        aggregations={
            "mean": [
                {"axis": "channels_y", "method": "median", "picks": "scalp"},
                _SCALP_MEAN,
                _MEAN_EPOCHS,
            ]
        },
    )
    out = marker.compute(_input(epochs))["mean"]
    assert out["col_names"] == ["wsmi"]
    assert 0 < out["data"][0] < 1


def test_wsmi_cache(epochs: Any) -> None:
    """Test that the wSMI is computed once for the same parameters."""
    estimator = SMIEstimator()
    estimator._compute.cache_clear()
    median = {"axis": "channels_y", "method": "median", "picks": "scalp"}
    scalar = EEGSymbolicMutualInformationScalar(
        aggregations={"mean": [median, _SCALP_MEAN, _MEAN_EPOCHS]}
    )
    topo = EEGSymbolicMutualInformationTopography(
        aggregations={"mean": [median, _MEAN_EPOCHS]}
    )
    scalar.compute(_input(epochs))
    topo.compute(_input(epochs))
    info = estimator._compute.cache_info()
    assert info.misses == 1
    assert info.hits == 1
    # Other parameters are computed again
    EEGSymbolicMutualInformationScalar(
        tau=4, aggregations={"mean": [median, _SCALP_MEAN, _MEAN_EPOCHS]}
    ).compute(_input(epochs))
    assert estimator._compute.cache_info().misses == 2


def test_marker_needs_epochs(epochs: Any) -> None:
    """Test the error with continuous data."""
    marker = EEGKolmogorovComplexityScalar(
        aggregations={"mean": [_SCALP_MEAN, _MEAN_EPOCHS]}
    )
    raw = epochs.average()
    with pytest.raises(TypeError, match="epoched data"):
        marker.compute(_input(raw))


def test_unknown_roi(epochs: Any) -> None:
    """Test the error with an ROI not defined for the montage."""
    marker = EEGKolmogorovComplexityScalar(
        aggregations={
            "mean": [
                {"axis": "channels", "method": "mean", "picks": "foo"},
                _MEAN_EPOCHS,
            ]
        }
    )
    with pytest.raises(ValueError, match="ROI foo not defined"):
        marker.compute(_input(epochs))
