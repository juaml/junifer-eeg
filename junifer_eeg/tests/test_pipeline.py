"""Provide tests for running the EEG pipeline with junifer."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.api import collect, run
from junifer.storage import HDF5FeatureStorage
from ruamel.yaml import YAML


_EXAMPLES = Path(__file__).parents[2] / "examples" / "yamls"


def test_run_icm_rs_config(raw_fif: Path, tmp_path: Path) -> None:
    """Test running the icm_rs configuration on synthetic data."""
    config = YAML().load(_EXAMPLES / "icm_rs.yaml")
    datagrabber = dict(config["datagrabber"])
    datagrabber["datadir"] = raw_fif
    datagrabber["patterns"] = {
        "EEG": {
            "pattern": "{subject}/{subject}_rs_raw.fif",
            "montage": "easycap-M1",
        },
    }
    preprocess = [dict(x) for x in config["preprocess"]]
    # Fewer epochs and channels in the synthetic data
    preprocess[0]["exclude"] = ["REF"]
    preprocess[-3]["min_epochs"] = 20
    markers = [dict(x) for x in config["markers"]]
    uri = tmp_path / "out" / "icm_rs.hdf5"
    run(
        workdir=tmp_path / "workdir",
        datagrabber=datagrabber,
        datareader=dict(config["datareader"]),
        preprocessors=preprocess,
        markers=markers,
        storage={"kind": "HDF5FeatureStorage", "uri": str(uri)},
    )
    collect(storage={"kind": "HDF5FeatureStorage", "uri": str(uri)})
    storage = HDF5FeatureStorage(uri=uri)
    names = {x["name"] for x in storage.list_features().values()}
    assert len(names) == 24
    psd = storage.read_df(feature_name="EEG_PSD_gfp_trim_mean80")
    assert sorted(psd.index.get_level_values("subject")) == [
        "sub-01",
        "sub-02",
    ]
    assert list(psd.columns)[:2] == ["delta", "deltan"]
    topo = storage.read_df(feature_name="EEG_wSMI_topo_std")
    assert topo.shape == (40, 1)
    assert topo.index.names == ["subject", "channel"]
