"""
Compute the spectral markers of TUEG recordings.
================================================

This example runs a junifer pipeline on clinical recordings of the TUH EEG
Corpus (TUEG): the spectral markers of the ICM resting state (the power in
each band, the spectral entropy and the spectral edges), with
:class:`.EEGAutoReject` instead of the adaptive rejection. The pipeline is the
same as the one of a YAML file (``junifer run``), given as Python objects.

Authors: Federico Raimondo

License: AGPL
"""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import mne
from junifer.api import collect, run
from junifer.storage import HDF5FeatureStorage
from junifer.utils import configure_logging

import junifer_eeg  # noqa: F401 (registers the components)
from junifer_eeg.datasets import fetch_tueg


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")

###############################################################################
# Download the first recording of some subjects
subjects = ["aaaaaaab", "aaaaaaaf", "aaaaaaag", "aaaaaaai"]
datadir = fetch_tueg(subjects)

###############################################################################
# Define the datagrabber and the preprocessing: the channels are renamed to
# the 10-20 names (``EEG FP1-REF`` to ``Fp1``), and the 19 channels of the
# 10-20 system are kept. See
# :ref:`sphx_glr_auto_examples_run_tueg_autoreject.py`
channels_1020 = [
    "Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "T3", "C3", "Cz", "C4", "T4",
    "T5", "P3", "Pz", "P4", "T6", "O1", "O2",
]  # fmt: skip

datagrabber = {
    "kind": "PatternDataGrabber",
    "datadir": str(datadir),
    "types": ["EEG"],
    "patterns": {
        "EEG": {
            "pattern": "000/{subject}/*/*/{subject}_*.edf",
            "montage": "colin27_1020",
        }
    },
    "replacements": ["subject"],
}

datareader = {"kind": "EEGDataReader"}

preprocessors = [
    {
        "kind": "EEGRenameChannels",
        "pattern": r"^EEG (\w+)-(REF|LE)$",
        "montage_case": True,
    },
    {"kind": "EEGPickChannels", "picks": channels_1020},
    {"kind": "EEGSetMontage"},
    {
        "kind": "EEGFilter",
        "l_freq": 0.5,
        "h_freq": None,
        "method": "iir",
        "iir_params": {"ftype": "butter", "order": 6},
    },
    {
        "kind": "EEGFilter",
        "l_freq": None,
        "h_freq": 45.0,
        "method": "iir",
        "iir_params": {"ftype": "butter", "order": 8},
    },
    # US power line
    {"kind": "EEGNotchFilter", "freqs": [60.0, 120.0], "method": "fft"},
    {"kind": "EEGResample", "sfreq": 250.0},
    # Pseudo-epochs of 800 ms (-200 to 600 ms), separated by 550 to 850 ms
    {
        "kind": "EEGFixedLengthEpochs",
        "duration": 0.8,
        "tmin": -0.2,
        "onset": 0.0,
        "jitter": [0.55, 0.85],
        "baseline": None,
        "seed": 42,
    },
    {"kind": "EEGAutoReject", "cv": 10, "seed": 42, "min_epochs": 0.3},
    {"kind": "EEGAverageReference"},
]

###############################################################################
# Define the markers: the PSD of each epoch and channel is reduced to scalars
# (the trimmed mean across epochs, then the mean across channels) and to
# topographies (the trimmed mean across epochs)
psd_params = {
    "estimator": {
        "method": "welch",
        "tmin": None,
        "tmax": 0.6,
        "fmin": 1.0,
        "fmax": 45.0,
        "method_params": {"n_fft": 4096, "n_overlap": 100, "nperseg": 128},
    },
    "bands": {
        "delta": [1.0, 4.0],
        "theta": [4.0, 8.0],
        "alpha": [8.0, 12.0],
        "beta": [12.0, 30.0],
        "gamma": [30.0, 45.0],
    },
    "dB": True,
    "normalized": True,
    "spectral_entropy": True,
    "spectral_edges": {"msf": 0.5, "sef90": 0.9, "sef95": 0.95},
}
trim_mean80 = {
    "axis": "epochs",
    "method": "trim_mean",
    "method_params": {"proportiontocut": 0.1},
}
channels_mean = {"axis": "channels", "method": "mean"}

markers = [
    {
        "name": "PSD",
        "kind": "EEGPowerSpectralDensityScalar",
        **psd_params,
        "aggregations": {"trim_mean80": [trim_mean80, channels_mean]},
    },
    {
        "name": "PSD_topo",
        "kind": "EEGPowerSpectralDensityTopography",
        **psd_params,
        "aggregations": {"trim_mean80": [trim_mean80]},
    },
]

###############################################################################
# Run the pipeline on each subject and collect the features in a single file
tmpdir = Path(tempfile.mkdtemp())
storage = {"kind": "HDF5FeatureStorage", "uri": str(tmpdir / "tueg.hdf5")}
run(
    workdir=tmpdir,
    datagrabber=datagrabber,
    datareader=datareader,
    preprocessors=preprocessors,
    markers=markers,
    storage=storage,
    elements=subjects,
)
collect(storage=storage, workdir=tmpdir)

###############################################################################
# Read the scalars: a row for each subject
features = HDF5FeatureStorage(uri=storage["uri"])
scalars = features.read_df(feature_name="EEG_PSD_trim_mean80")
print(scalars.round(2))

###############################################################################
# Plot the normalized power in the delta and the alpha band (the fraction of
# the power from 1 to 45 Hz) of each subject. The subjects with more delta
# have less alpha: their EEG is slower
fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
ax.scatter(scalars["deltan"], scalars["alphan"])
for subject, x, y in zip(
    scalars.index.get_level_values("subject"),
    scalars["deltan"],
    scalars["alphan"],
    strict=True,
):
    ax.annotate(subject, (x, y))
ax.set(xlabel="Normalized delta power", ylabel="Normalized alpha power")

###############################################################################
# Plot the topographies of the normalized alpha power: a row for each channel
# and subject
topos = features.read_df(feature_name="EEG_PSD_topo_trim_mean80")
ch_names = topos.loc[subjects[0]].index.tolist()
info = mne.create_info(ch_names, sfreq=250.0, ch_types="eeg")
info.set_montage("colin27_1020")
alphan = topos["alphan"]
vlim = (alphan.min(), alphan.max())
fig, axes = plt.subplots(1, len(subjects), figsize=(10, 3))
for ax, subject in zip(axes, subjects, strict=True):
    im, _ = mne.viz.plot_topomap(
        alphan.loc[subject].values, info, axes=ax, vlim=vlim, show=False
    )
    ax.set_title(subject)
fig.colorbar(im, ax=axes, label="Normalized alpha power", shrink=0.8)
