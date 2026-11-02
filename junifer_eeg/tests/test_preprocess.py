"""Provide tests for the EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import mne
import numpy as np
import pytest

from junifer_eeg.conftest import make_epochs, make_raw
from junifer_eeg.preprocess import (
    EEGAdaptiveRejection,
    EEGAverageReference,
    EEGFilter,
    EEGFixedLengthEpochs,
    EEGInterpolateBads,
    EEGNotchFilter,
    EEGPickChannels,
    EEGRenameChannels,
    EEGResample,
    EEGSetMontage,
)


def _input(inst: Any) -> dict[str, Any]:
    """Get the data object for the data."""
    return {"EEG": {"data": inst, "montage": "easycap-M1", "meta": {}}}


def _run(preprocessor: Any, inst: Any) -> Any:
    """Run a preprocessor on the data."""
    out = preprocessor.fit_transform(_input(inst))
    meta = out["EEG"]["meta"]["preprocess"][-1]
    assert meta["class"] == preprocessor.__class__.__name__
    return out["EEG"]["data"]


def test_pick_channels_and_montage() -> None:
    """Test picking the EEG channels and setting the montage."""
    raw = make_raw(duration=5, extra_channels=True)
    raw = _run(EEGPickChannels(exclude=["REF", "VREF"]), raw)
    assert "REF" not in raw.ch_names
    assert "ECG" not in raw.ch_names
    assert len(raw.ch_names) == 20
    raw = _run(EEGSetMontage(), raw)
    assert raw.get_montage() is not None


def test_rename_channels() -> None:
    """Test renaming the channels to the names of the montage."""
    raw = make_raw(duration=5)
    # As in clinical EDF files (e.g., TUEG)
    raw.rename_channels({x: f"EEG {x.upper()}-REF" for x in raw.ch_names})
    raw = _run(
        EEGRenameChannels(
            pattern=r"^EEG (\w+)-REF$",
            mapping={"OZ": "Oz2"},
            montage_case=True,
        ),
        raw,
    )
    assert raw.ch_names[:3] == ["Fp1", "Fp2", "F7"]
    # The mapping is applied before the case of the montage
    assert "Oz2" in raw.ch_names
    raw.rename_channels({"Fp2": "x", "F7": "X"})
    with pytest.raises(ValueError, match="same names"):
        _run(EEGRenameChannels(mapping={"x": "X"}), raw)


def test_filters_and_resample() -> None:
    """Test filtering and resampling."""
    raw = make_raw(duration=10)
    raw = _run(
        EEGFilter(
            l_freq=0.5,
            h_freq=None,
            method="iir",
            iir_params={"ftype": "butter", "order": 6},
        ),
        raw,
    )
    raw = _run(EEGNotchFilter(freqs=[50.0, 100.0]), raw)
    assert raw.info["highpass"] == 0.5
    raw = _run(EEGResample(sfreq=250.0), raw)
    assert raw.info["sfreq"] == 250.0
    raw = _run(EEGResample(sfreq=125.0), raw)
    assert raw.info["sfreq"] == 125.0


def test_fixed_length_epochs() -> None:
    """Test the jittered pseudo-epochs."""
    raw = make_raw(duration=60)
    params = {
        "duration": 0.8,
        "tmin": -0.2,
        "jitter": [0.55, 0.85],
        "seed": 42,
    }
    epochs = _run(EEGFixedLengthEpochs(**params), raw.copy())
    assert isinstance(epochs, mne.BaseEpochs)
    assert len(epochs.times) == 201
    # The first event is at 0, so its epoch (from -0.2 s) is out of the data
    assert epochs.drop_log[0] == ("NO_DATA",)
    gaps = np.diff(epochs.events[:, 0])
    assert gaps.min() >= 200 + 138
    assert gaps.max() <= 200 + 213
    # Same epochs with the same seed, different with another one
    again = _run(EEGFixedLengthEpochs(**params), raw.copy())
    np.testing.assert_array_equal(epochs.events, again.events)
    other = _run(EEGFixedLengthEpochs(**{**params, "seed": 1}), raw.copy())
    assert not np.array_equal(epochs.events[:, 0], other.events[:5, 0])
    with pytest.raises(ValueError, match="jitter"):
        EEGFixedLengthEpochs(duration=1.0, jitter=[0.8, 0.5])


def test_wrong_instance() -> None:
    """Test the error with the wrong type of data."""
    epochs = make_epochs()
    with pytest.raises(TypeError, match="needs BaseRaw data"):
        _run(EEGFilter(l_freq=1.0, h_freq=None), epochs)
    with pytest.raises(TypeError, match="needs BaseEpochs data"):
        _run(EEGAdaptiveRejection(reject={"eeg": 1e-4}), make_raw(5))


def test_adaptive_rejection() -> None:
    """Test the adaptive rejection of channels and epochs."""
    epochs = make_epochs(n_epochs=40)
    data = epochs.get_data()
    # A noisy channel and two artifacted epochs
    data[:, 3] *= 50
    data[5, :10, 100:] += 1e-3
    data[7, :10, 100:] += 1e-3
    epochs = mne.EpochsArray(data, epochs.info, tmin=-0.2, verbose="error")
    rejection = EEGAdaptiveRejection(
        reject={"eeg": 100e-6},
        min_channels=0.7,
        min_epochs=30,
    )
    epochs = _run(rejection, epochs)
    assert epochs.ch_names[3] in epochs.info["bads"]
    assert len(epochs) == 38
    assert epochs.drop_log[5] == ("artifacted",)


def test_adaptive_rejection_gates() -> None:
    """Test the rejection of the subjects."""
    with pytest.raises(RuntimeError, match="epochs remain"):
        _run(
            EEGAdaptiveRejection(reject={"eeg": 100e-6}, min_epochs=1000),
            make_epochs(),
        )
    with pytest.raises(RuntimeError, match="channels are good"):
        _run(
            EEGAdaptiveRejection(reject={"eeg": 1e-9}, min_channels=0.7),
            make_epochs(),
        )


def test_reference_and_interpolation() -> None:
    """Test the average reference and the interpolation."""
    raw = make_raw(duration=10)
    raw.set_montage("easycap-M1")
    raw.info["bads"] = ["Cz"]
    epochs = mne.make_fixed_length_epochs(raw, 1.0, preload=True)
    epochs = _run(EEGAverageReference(), epochs)
    good = mne.pick_types(epochs.info, eeg=True, exclude="bads")
    np.testing.assert_allclose(
        epochs.get_data()[:, good].mean(axis=1), 0, atol=1e-18
    )
    epochs = _run(EEGInterpolateBads(), epochs)
    assert epochs.info["bads"] == []
