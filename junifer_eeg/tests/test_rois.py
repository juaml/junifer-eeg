"""Provide tests for the ROIs of the montages."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import mne
import pytest
from ruamel.yaml import YAML

from junifer_eeg.conftest import _TEST_MONTAGE, _TEST_ROIS
from junifer_eeg.data import EEGROIRegistry, get_roi_channels


_ROIS_DIR = Path(__file__).parents[1] / "data" / "rois"


def _read(fname: Path) -> dict:
    """Read a file of built-in ROIs."""
    with fname.open() as f:
        return YAML(typ="safe").load(f)


@pytest.mark.parametrize(
    "fname", sorted(_ROIS_DIR.glob("*.yaml")), ids=lambda x: x.stem
)
def test_builtin_rois(fname: Path) -> None:
    """Test that the ROIs have channels of their montages."""
    content = _read(fname)
    assert set(content) == {"system", "montages", "rois"}
    rois = content["rois"]
    for name in ["scalp", "fz", "cz", "pz"]:
        assert name in rois
    # Lowercase, not to be taken for the channel names in the picks
    assert all(x == x.lower() for x in rois)
    # The channels of all the montages
    ch_names = set()
    for montage in content["montages"]:
        ch_names |= set(mne.channels.make_standard_montage(montage).ch_names)
    for name, channels in rois.items():
        assert len(channels) > 0
        assert len(set(channels)) == len(channels)
        assert set(channels) <= ch_names, name
        if name not in ("scalp", "nonscalp"):
            assert set(channels) <= set(rois["scalp"]), name
    assert set(rois["scalp"]).isdisjoint(rois.get("nonscalp", []))
    # Registered for all the montages (but the ROIs of the tests)
    registry = EEGROIRegistry()
    for montage in content["montages"]:
        for name, channels in rois.items():
            if montage == _TEST_MONTAGE and name in _TEST_ROIS:
                continue
            assert registry.load(montage, name) == channels


def test_roi_channels() -> None:
    """Test that the ROIs keep the channels in the data."""
    registry = EEGROIRegistry()
    target = {"montage": "colin27_1020"}
    fz = registry.load("colin27_1020", "fz")
    # A 10-20 cap: the ROI has the 10-05 positions
    ch_names = ["Fp1", "Fp2", "F3", "Fz", "F4", "C3", "Cz", "C4"]
    assert get_roi_channels("fz", target, ch_names) == ["F3", "Fz", "F4"]
    assert get_roi_channels("fz", target) == fz
    with pytest.raises(ValueError, match="No channel of the ROI fz"):
        get_roi_channels("fz", target, ["O1", "O2"])
    # The channel names are kept
    assert get_roi_channels(["O1", "O2"], target, ["O1"]) == ["O1", "O2"]
    assert get_roi_channels("Fz", target, ch_names) == ["Fz"]


def test_roi_channels_concatenated() -> None:
    """Test the concatenation of ROIs and channels, without repetitions."""
    target = {"montage": "colin27_1020"}
    ch_names = ["Fp1", "Fp2", "F3", "Fz", "F4", "C3", "Cz", "C4", "Pz", "Oz"]
    assert get_roi_channels(["fz", "cz"], target, ch_names) == [
        "F3", "Fz", "F4", "C3", "Cz", "C4",
    ]  # fmt: skip
    assert get_roi_channels(["fz", "Oz", "Fz"], target, ch_names) == [
        "F3", "Fz", "F4", "Oz",
    ]  # fmt: skip
