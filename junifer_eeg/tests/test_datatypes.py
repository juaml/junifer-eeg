"""Provide tests for the EEG data type."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from junifer.datagrabber import DataTypeManager

from junifer_eeg.datatypes import get_eeg_companions


def _touch(path: Path, text: str = "") -> Path:
    """Create a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.mark.skipif(
    not hasattr(DataTypeManager, "get_companions"),
    reason="junifer without the companions (juaml/junifer#539)",
)
def test_eeg_companions_registered() -> None:
    """Test the companions of the EEG data type are registered."""
    assert DataTypeManager().get_companions("EEG") is get_eeg_companions


def test_brainvision_companions(tmp_path: Path) -> None:
    """Test the data and marker files of a BrainVision header."""
    vhdr = _touch(
        tmp_path / "sub-01_eeg.vhdr",
        "Brain Vision Data Exchange Header File Version 1.0\n"
        "; Data created by the Vision Recorder\n\n"
        "[Common Infos]\n"
        "Codepage=UTF-8\n"
        "DataFile=$b.eeg\n"
        "MarkerFile=markers.vmrk\n"
        "DataFormat=BINARY\n",
    )
    assert get_eeg_companions(vhdr) == [
        tmp_path / "sub-01_eeg.eeg",
        tmp_path / "markers.vmrk",
    ]


def test_eeglab_companions(tmp_path: Path) -> None:
    """Test the data file of an EEGLAB dataset."""
    single = _touch(tmp_path / "single.set")
    assert get_eeg_companions(single) == []
    two_files = _touch(tmp_path / "two_files.set")
    fdt = _touch(tmp_path / "two_files.fdt")
    assert get_eeg_companions(two_files) == [fdt]


def test_fif_companions(tmp_path: Path) -> None:
    """Test the split files of a FIF file."""
    # MNE
    fif = _touch(tmp_path / "rec_raw.fif")
    assert get_eeg_companions(fif) == []
    splits = [_touch(tmp_path / f"rec_raw-{i}.fif") for i in [1, 2]]
    assert get_eeg_companions(fif) == splits
    # BIDS
    names = [f"sub-01_task-rest_split-{i:02d}_eeg.fif" for i in [1, 2, 3]]
    bids = [_touch(tmp_path / "bids" / x) for x in names]
    assert get_eeg_companions(bids[0]) == bids[1:]
    assert get_eeg_companions(bids[1]) == bids[2:]
    # A link to a file not got (e.g., in a DataLad dataset)
    link = tmp_path / "rec_raw-3.fif"
    link.symlink_to(tmp_path / "missing")
    assert get_eeg_companions(fif) == [*splits, link]


def test_no_companions(tmp_path: Path) -> None:
    """Test the recordings without companion files."""
    assert get_eeg_companions(_touch(tmp_path / "rec.edf")) == []
    mff = tmp_path / "rec.mff"
    _touch(mff / "signal1.bin")
    assert get_eeg_companions(mff) == []
