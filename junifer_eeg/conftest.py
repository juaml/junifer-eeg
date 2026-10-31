"""Provide conftest for pytest."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import mne
import numpy as np
import pytest

import junifer_eeg  # noqa: F401
from junifer_eeg.data import EEGROIRegistry


# Small montage for the tests, with ROIs
_TEST_MONTAGE = "easycap-M1"
_TEST_CHANNELS = [
    "Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "T7", "C3", "Cz",
    "C4", "T8", "P7", "P3", "Pz", "P4", "P8", "O1", "Oz", "O2",
]  # fmt: skip
_TEST_ROIS = {
    "scalp": _TEST_CHANNELS[:-3],
    "frontal": ["Fp1", "Fp2", "F3", "Fz", "F4"],
}


@pytest.fixture(scope="session", autouse=True)
def test_rois() -> None:
    """Register the ROIs of the test montage."""
    registry = EEGROIRegistry()
    for name, ch_names in _TEST_ROIS.items():
        registry.register(_TEST_MONTAGE, name, ch_names, overwrite=True)


def make_raw(
    duration: float = 60.0,
    sfreq: float = 250.0,
    seed: int = 42,
    extra_channels: bool = False,
) -> mne.io.RawArray:
    """Make a synthetic EEG recording.

    Parameters
    ----------
    duration : float, optional
        The duration in seconds (default 60.0).
    sfreq : float, optional
        The sampling frequency (default 250.0).
    seed : int, optional
        The random seed (default 42).
    extra_channels : bool, optional
        Whether to add a reference and an ECG channel (default False).

    Returns
    -------
    mne.io.RawArray
        The recording, without montage.

    """
    rng = np.random.default_rng(seed)
    n_times = int(duration * sfreq)
    times = np.arange(n_times) / sfreq
    ch_names = list(_TEST_CHANNELS)
    # Alpha oscillation (with a different phase in each channel, so it is
    # not removed by the average reference) and pink-ish noise, in V
    phases = rng.uniform(0, 2 * np.pi, (len(ch_names), 1))
    alpha = np.sin(2 * np.pi * 10 * times + phases)
    data = np.cumsum(rng.standard_normal((len(ch_names), n_times)), axis=1)
    data -= data.mean(axis=1, keepdims=True)
    data = 1e-6 * (0.5 * data / data.std(axis=1, keepdims=True) + 3 * alpha)
    ch_types = ["eeg"] * len(ch_names)
    if extra_channels:
        data = np.vstack([data, rng.standard_normal((2, n_times)) * 1e-6])
        ch_names += ["REF", "ECG"]
        ch_types += ["eeg", "ecg"]
    info = mne.create_info(ch_names, sfreq, ch_types)
    return mne.io.RawArray(data, info, verbose="error")


def make_epochs(
    n_epochs: int = 20, seed: int = 42, sfreq: float = 250.0
) -> mne.EpochsArray:
    """Make synthetic EEG epochs of 0.8 s (from -0.2 s), with montage.

    Parameters
    ----------
    n_epochs : int, optional
        The number of epochs (default 20).
    seed : int, optional
        The random seed (default 42).
    sfreq : float, optional
        The sampling frequency (default 250.0).

    Returns
    -------
    mne.EpochsArray
        The epochs.

    """
    raw = make_raw(duration=n_epochs * 0.81, sfreq=sfreq, seed=seed)
    n_times = round(0.8 * sfreq) + 1
    data = np.stack(
        [
            raw.get_data()[:, i * n_times : (i + 1) * n_times]
            for i in range(n_epochs)
        ]
    )
    epochs = mne.EpochsArray(data, raw.info, tmin=-0.2, verbose="error")
    epochs.set_montage(_TEST_MONTAGE)
    epochs.set_eeg_reference("average", projection=True, verbose="error")
    return epochs.apply_proj(verbose="error")


@pytest.fixture
def raw_fif(tmp_path: Path) -> Path:
    """Write a synthetic recording for two subjects, as FIF files."""
    for subject in ["sub-01", "sub-02"]:
        raw = make_raw(seed=int(subject[-1]), extra_channels=True)
        (tmp_path / subject).mkdir()
        raw.save(tmp_path / subject / f"{subject}_rs_raw.fif", verbose="error")
    return tmp_path
