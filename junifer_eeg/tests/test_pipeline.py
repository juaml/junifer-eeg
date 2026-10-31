"""Provide tests for running the EEG pipeline with junifer."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.api import collect, run
from junifer.storage import HDF5FeatureStorage
from ruamel.yaml import YAML


# The ICM resting-state pipeline of NICE (`icm/rs`), for the synthetic data
_CONFIG = """
definitions:
  psd_params: &psd_params
    estimator:
      method: welch
      tmin: null
      tmax: 0.6
      fmin: 1.0
      fmax: 45.0
      method_params: {n_fft: 4096, n_overlap: 100, nperseg: 128}
    bands:
      delta: [1.0, 4.0]
      theta: [4.0, 8.0]
      alpha: [8.0, 12.0]
      beta: [12.0, 30.0]
      gamma: [30.0, 45.0]
    dB: true
    normalized: true
    spectral_entropy: true
    spectral_edges: {msf: 0.5, sef90: 0.9, sef95: 0.95}
  pe_params: &pe_params {tmin: null, tmax: 0.6, kernel: 3, tau: 8}
  wsmi_params: &wsmi_params
    {tmin: null, tmax: 0.6, kernel: 3, tau: 8, method: weighted, csd: true}
  kc_params: &kc_params {tmin: null, tmax: 0.6, nbins: 32}
  scalp_mean: &scalp_mean {axis: channels, method: mean, picks: scalp}
  scalp_std: &scalp_std {axis: channels, method: std, picks: scalp}
  trim_mean80: &trim_mean80
    {axis: epochs, method: trim_mean, method_params: {proportiontocut: 0.1}}
  epochs_std: &epochs_std {axis: epochs, method: std}
  connected_median: &connected_median
    {axis: channels_y, method: median, picks: scalp}
  scalar: &scalar
    trim_mean80: [*trim_mean80, *scalp_mean]
    std: [*epochs_std, *scalp_mean]
    gfp_trim_mean80: [*trim_mean80, *scalp_std]
    gfp_std: [*epochs_std, *scalp_std]
  topo: &topo
    trim_mean80: [*trim_mean80]
    std: [*epochs_std]

datareader:
  kind: EEGDataReader

preprocess:
  - {kind: EEGPickChannels, picks: eeg, exclude: [REF]}
  - kind: EEGSetMontage
  - kind: EEGFilter
    l_freq: 0.5
    h_freq: null
    method: iir
    iir_params: {ftype: butter, order: 6}
  - kind: EEGFilter
    l_freq: null
    h_freq: 45.0
    method: iir
    iir_params: {ftype: butter, order: 8}
  - {kind: EEGNotchFilter, freqs: [50.0, 100.0], method: fft}
  - {kind: EEGResample, sfreq: 250.0}
  - kind: EEGFixedLengthEpochs
    duration: 0.8
    tmin: -0.2
    onset: 0.0
    jitter: [0.55, 0.85]
    baseline: null
    seed: 42
  - kind: EEGAdaptiveRejection
    reject: {eeg: 100.0e-6}
    n_epochs_bad_ch: 0.5
    n_channels_bad_epoch: 0.1
    zscore_thresh: 4
    max_iter: 4
    min_channels: 0.7
    min_epochs: 20
  - kind: EEGAverageReference
  - {kind: EEGInterpolateBads, reset_bads: true}

markers:
  - {name: PSD, kind: EEGPowerSpectralDensityScalar, <<: *psd_params,
     aggregations: *scalar}
  - {name: PSD_topo, kind: EEGPowerSpectralDensityTopography,
     <<: *psd_params, aggregations: *topo}
  - {name: PE, kind: EEGPermutationEntropyScalar, <<: *pe_params,
     aggregations: *scalar}
  - {name: PE_topo, kind: EEGPermutationEntropyTopography, <<: *pe_params,
     aggregations: *topo}
  - name: wSMI
    kind: EEGSymbolicMutualInformationScalar
    <<: *wsmi_params
    aggregations:
      trim_mean80: [*trim_mean80, *connected_median, *scalp_mean]
      std: [*epochs_std, *connected_median, *scalp_mean]
      gfp_trim_mean80: [*trim_mean80, *connected_median, *scalp_std]
      gfp_std: [*epochs_std, *connected_median, *scalp_std]
  - name: wSMI_topo
    kind: EEGSymbolicMutualInformationTopography
    <<: *wsmi_params
    aggregations:
      trim_mean80: [*trim_mean80, *connected_median]
      std: [*epochs_std, *connected_median]
  - {name: KC, kind: EEGKolmogorovComplexityScalar, <<: *kc_params,
     aggregations: *scalar}
  - {name: KC_topo, kind: EEGKolmogorovComplexityTopography, <<: *kc_params,
     aggregations: *topo}
"""


def test_run_icm_rs_config(raw_fif: Path, tmp_path: Path) -> None:
    """Test running the ICM resting-state pipeline on synthetic data."""
    config = YAML(typ="safe").load(_CONFIG)
    datagrabber = {
        "kind": "PatternDataGrabber",
        "datadir": raw_fif,
        "types": ["EEG"],
        "patterns": {
            "EEG": {
                "pattern": "{subject}/{subject}_rs_raw.fif",
                "montage": "easycap-M1",
            },
        },
        "replacements": ["subject"],
    }
    preprocess = config["preprocess"]
    markers = config["markers"]
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
