"""
Preprocess a TUEG recording with autoreject.
============================================

This example preprocesses a clinical recording of the TUH EEG Corpus (TUEG),
applying the preprocessing steps one by one: the channels are renamed to the
10-20 names, the 19 channels of the 10-20 system are kept, and the
pseudo-epochs of the resting state are repaired or rejected with
:class:`.EEGAutoReject`.

Authors: Federico Raimondo

License: AGPL
"""

import matplotlib.pyplot as plt
import numpy as np
from junifer.datagrabber import PatternDataGrabber
from junifer.utils import configure_logging

from junifer_eeg.datareader import EEGDataReader
from junifer_eeg.datasets import fetch_tueg
from junifer_eeg.preprocess import (
    EEGAutoReject,
    EEGFilter,
    EEGFixedLengthEpochs,
    EEGNotchFilter,
    EEGPickChannels,
    EEGRenameChannels,
    EEGResample,
    EEGSetMontage,
)


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")

###############################################################################
# Download the first recording of a subject. The recordings keep the layout of
# the corpus: ``<group>/<subject>/<session>/<montage>/<recording>.edf``
datadir = fetch_tueg(["aaaaaaai"])

datagrabber = PatternDataGrabber(
    datadir=datadir,
    types=["EEG"],
    patterns={
        "EEG": {
            "pattern": "000/{subject}/*/*/{subject}_*.edf",
            "montage": "colin27_1020",
        }
    },
    replacements=["subject"],
)

###############################################################################
# Read the recording. The EEG channels are named as ``EEG FP1-REF`` (or
# ``EEG FP1-LE``, for the linked-ears reference), and there are non-EEG
# channels (e.g., the ECG)
with datagrabber:
    element_data = EEGDataReader().fit_transform(datagrabber["aaaaaaai"])
raw = element_data["EEG"]["data"]
print(raw.ch_names)

###############################################################################
# Rename the channels to the names of the montage (``EEG FP1-REF`` to
# ``Fp1``), keep the 19 channels of the 10-20 system and set the montage
channels_1020 = [
    "Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "T3", "C3", "Cz", "C4", "T4",
    "T5", "P3", "Pz", "P4", "T6", "O1", "O2",
]  # fmt: skip
EEGRenameChannels(
    pattern=r"^EEG (\w+)-(REF|LE)$", montage_case=True
).fit_transform(element_data)
EEGPickChannels(picks=channels_1020).fit_transform(element_data)
EEGSetMontage().fit_transform(element_data)
print(element_data["EEG"]["data"].ch_names)

###############################################################################
# Filter (0.5 to 45 Hz, and the US power line), resample to 250 Hz and cut the
# pseudo-epochs of 800 ms, as in the ICM resting state
steps = [
    EEGFilter(
        l_freq=0.5,
        h_freq=None,
        method="iir",
        iir_params={"ftype": "butter", "order": 6},
    ),
    EEGFilter(
        l_freq=None,
        h_freq=45.0,
        method="iir",
        iir_params={"ftype": "butter", "order": 8},
    ),
    EEGNotchFilter(freqs=[60.0, 120.0], method="fft"),
    EEGResample(sfreq=250.0),
    EEGFixedLengthEpochs(
        duration=0.8,
        tmin=-0.2,
        onset=0.0,
        jitter=[0.55, 0.85],
        baseline=None,
        seed=42,
    ),
]
for step in steps:
    step.fit_transform(element_data)
epochs = element_data["EEG"]["data"].copy()
print(epochs)

###############################################################################
# Repair or reject the epochs with autoreject. The thresholds of each channel
# are learnt by cross-validation: the bad channels of an epoch are
# interpolated, and the epochs with too many bad channels are dropped
EEGAutoReject(cv=10, seed=42, min_epochs=0.3).fit_transform(element_data)
cleaned = element_data["EEG"]["data"]
print(cleaned)

###############################################################################
# Plot the peak-to-peak amplitude of each epoch (the largest of the channels),
# before and after autoreject
kept = np.isin(epochs.selection, cleaned.selection)
ptp = np.ptp(epochs.get_data(), axis=-1).max(axis=-1) * 1e6
ptp_cleaned = np.full(len(epochs), np.nan)
ptp_cleaned[kept] = np.ptp(cleaned.get_data(), axis=-1).max(axis=-1) * 1e6
fig, ax = plt.subplots(figsize=(8, 3), layout="constrained")
ax.plot(ptp, color="0.7", label="Before")
ax.plot(ptp_cleaned, color="C0", label="After (repaired)")
dropped = np.flatnonzero(~kept)
ax.plot(dropped, ptp[dropped], "x", color="C3", label="Dropped")
ax.set(xlabel="Epoch", ylabel="Peak-to-peak (µV)")
ax.legend()

###############################################################################
# Plot the PSD of the epochs, before and after autoreject
fig, axes = plt.subplots(2, 1, figsize=(8, 6), layout="constrained")
for ax, inst, title in zip(
    axes, [epochs, cleaned], ["Before", "After"], strict=True
):
    inst.compute_psd(fmin=1.0, fmax=45.0).plot(axes=ax, show=False)
    ax.set_title(title)
