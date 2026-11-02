"""Provide tests for the testing components."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import numpy as np
import pytest
from junifer.api import collect, run
from junifer.pipeline import PipelineComponentRegistry
from junifer.storage import HDF5FeatureStorage

import junifer_eeg.testing.registry  # noqa: F401
from junifer_eeg.testing.datagrabbers import TUEGTestingDataGrabber


def _fake_recordings(datadir: Path, subjects: list[str]) -> list[Path]:
    """Create fake recordings, as downloaded (two for each subject)."""
    out = []
    for subject in subjects:
        t_dir = datadir / "v2.0.2/edf/000" / subject / "s001_2002/02_tcp_le"
        t_dir.mkdir(parents=True)
        for token in ["t001", "t000"]:
            (t_dir / f"{subject}_s001_{token}.edf").write_bytes(b"EDF")
        out.append(t_dir / f"{subject}_s001_t000.edf")
    return out


def test_tueg_testing_datagrabber(tmp_path: Path) -> None:
    """Test the TUEG DataGrabber, with the recordings downloaded."""
    subjects = ["aaaaaaaf", "aaaaaaab"]
    fnames = _fake_recordings(tmp_path, subjects)
    dg = TUEGTestingDataGrabber(datadir=tmp_path, subjects=subjects)
    assert dg.get_types() == ["EEG"]
    with dg:
        assert dg.get_elements() == subjects
        for subject, fname in zip(subjects, fnames, strict=True):
            out = dg[subject]
            assert list(out) == ["EEG"]
            # The first recording
            assert out["EEG"]["path"] == fname
            assert out["EEG"]["montage"] == "colin27_1020"
            assert out["EEG"]["meta"]["element"] == {"subject": subject}


def test_tueg_testing_datagrabber_context(tmp_path: Path) -> None:
    """Test the TUEG DataGrabber needs the context (the download)."""
    _fake_recordings(tmp_path, ["aaaaaaaf"])
    dg = TUEGTestingDataGrabber(datadir=tmp_path, subjects=["aaaaaaaf"])
    with pytest.raises(RuntimeError, match="context manager"):
        dg["aaaaaaaf"]


def test_testing_registry() -> None:
    """Test the testing DataGrabbers are registered."""
    registry = PipelineComponentRegistry()
    assert (
        registry.get_class(step="datagrabber", name="TUEGTestingDataGrabber")
        is TUEGTestingDataGrabber
    )


@pytest.mark.external
def test_tueg_testing_datagrabber_run(tmp_path: Path) -> None:
    """Test a pipeline on a TUEG recording (downloaded)."""
    storage = {"kind": "HDF5FeatureStorage", "uri": str(tmp_path / "f.hdf5")}
    run(
        workdir=tmp_path,
        datagrabber={
            "kind": "TUEGTestingDataGrabber",
            "subjects": ["aaaaaaag"],
        },
        datareader={"kind": "EEGDataReader"},
        preprocessors=[
            {
                "kind": "EEGRenameChannels",
                "pattern": r"^EEG (\w+)-(REF|LE)$",
                "montage_case": True,
            },
            {"kind": "EEGPickChannels", "picks": ["Fp1", "Fz", "Cz", "O1"]},
            {"kind": "EEGSetMontage"},
            {"kind": "EEGFixedLengthEpochs", "duration": 1.0},
        ],
        markers=[
            {
                "name": "PSD",
                "kind": "EEGPowerSpectralDensityScalar",
                "estimator": {"method": "welch", "fmin": 1.0, "fmax": 45.0},
                "bands": {"alpha": [8.0, 12.0]},
                "aggregations": {
                    "mean": [
                        {"axis": "epochs", "method": "mean"},
                        {"axis": "channels", "method": "mean"},
                    ]
                },
            }
        ],
        storage=storage,
        elements=["aaaaaaag"],
    )
    collect(storage=storage)
    df = HDF5FeatureStorage(uri=storage["uri"]).read_df(
        feature_name="EEG_PSD_mean"
    )
    assert df.index.get_level_values("subject").tolist() == ["aaaaaaag"]
    assert np.isfinite(df["alpha"]).all()
