"""Provide tests for the EEG DataReader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import zipfile
from pathlib import Path

import mne
import pytest
from junifer.pipeline import WorkDirManager

from junifer_eeg.datareader import EEGDataReader
from junifer_eeg.datareader.eeg import _extract_mff_zip, _get_format


@pytest.mark.parametrize(
    "fname, format, expected",
    [
        ("sub-01-icm-rs-egi.mff.zip", None, "egi"),
        ("sub-01.mff", None, "egi"),
        ("sub-01_raw.fif", None, "fif"),
        ("sub-01_raw.FIF.gz", None, "fif"),
        ("sub-01.vhdr", None, "brainvision"),
        ("sub-01-icm-rs-egi.raw", "egi", "egi"),
    ],
)
def test_get_format(fname: str, format: str | None, expected: str) -> None:
    """Test the format of the EEG files."""
    assert _get_format(Path(fname), format) == expected


def test_get_format_errors() -> None:
    """Test the errors for unknown formats."""
    with pytest.raises(ValueError, match="Cannot guess the format"):
        _get_format(Path("sub-01-icm-rs-egi.raw"), None)
    with pytest.raises(ValueError, match="Unknown EEG format"):
        _get_format(Path("sub-01.raw"), "foo")


def test_extract_mff_zip(tmp_path: Path) -> None:
    """Test extracting a zipped MFF directory, as saved by macOS."""
    WorkDirManager().workdir = tmp_path / "workdir"
    fname = tmp_path / "sub-01-icm-rs-egi.mff.zip"
    with zipfile.ZipFile(fname, "w") as zf:
        zf.writestr("CB3 0101 0236/info.xml", "<xml/>")
        zf.writestr("__MACOSX/CB3 0101 0236/._info.xml", "")
        zf.writestr(".DS_Store", "")
    mff_dir = _extract_mff_zip(fname)
    assert mff_dir.name == "CB3 0101 0236.mff"
    assert (mff_dir / "info.xml").exists()

    fname = tmp_path / "two.mff.zip"
    with zipfile.ZipFile(fname, "w") as zf:
        zf.writestr("a/info.xml", "<xml/>")
        zf.writestr("b/info.xml", "<xml/>")
    with pytest.raises(ValueError, match="must contain one MFF directory"):
        _extract_mff_zip(fname)


def test_eeg_datareader(raw_fif: Path) -> None:
    """Test reading EEG and other data types."""
    fname = raw_fif / "sub-01" / "sub-01_rs_raw.fif"
    tsv = raw_fif / "sub-01" / "events.tsv"
    tsv.write_text("onset\tduration\n1.0\t0.5\n")
    input = {
        "EEG": {
            "path": str(fname),
            "montage": "easycap-M1",
            "meta": {"datagrabber": {}},
        },
        "Events": {"path": tsv, "meta": {}},
    }
    out = EEGDataReader().fit_transform(input)
    assert isinstance(out["EEG"]["data"], mne.io.BaseRaw)
    assert out["EEG"]["data"].preload
    assert out["EEG"]["path"] == fname
    assert out["EEG"]["meta"]["datareader"]["class"] == "EEGDataReader"
    assert "junifer_eeg" in out["EEG"]["meta"]["dependencies"]
    assert out["Events"]["data"].shape == (1, 2)
