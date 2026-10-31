"""Provide tests for the event-related EEG components."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pytest
from junifer.storage import StorageType

from junifer_eeg.conftest import _TEST_MONTAGE, _TEST_ROIS, make_raw
from junifer_eeg.datareader.eeg import _read_eeg_files
from junifer_eeg.markers import (
    EEGContingentNegativeVariationScalar,
    EEGContingentNegativeVariationTimeseries,
    EEGEventRelatedContrastScalar,
    EEGEventRelatedContrastTopography,
    EEGEventRelatedPotentialScalar,
    EEGEventRelatedPotentialTopography,
    EEGWindowDecodingScalar,
)
from junifer_eeg.preprocess import (
    EEGDropEvents,
    EEGEventEpochs,
    EEGRenameEvents,
)
from junifer_eeg.tests import _nice_reference as nice


_EVENT_ID = {"STD": 1, "DEV": 2}
_MEAN = {"method": "mean"}


def _input(inst: Any) -> dict[str, Any]:
    """Get the data object item for an MNE object."""
    return {"data": inst, "montage": _TEST_MONTAGE, "meta": {}}


def _block(seed: int, labels: list[str]) -> mne.io.RawArray:
    """Make a block of 20 s with an event every second."""
    raw = make_raw(duration=20.0, seed=seed)
    raw.set_annotations(
        mne.Annotations(
            onset=np.arange(1.0, 1.0 + len(labels)),
            duration=0.0,
            description=labels,
        )
    )
    return raw


def _make_epochs(seed: int = 0) -> mne.Epochs:
    """Make epochs (-0.2 to 1 s) with a deviant response on the DEV events.

    The DEV epochs have a positive deflection between 0.3 and 0.5 s in the
    frontal ROI.

    """
    rng = np.random.default_rng(seed)
    labels = list(rng.choice(["STD", "DEV"], size=60, p=[0.7, 0.3]))
    raw = make_raw(duration=65.0, seed=seed)
    raw.set_montage(_TEST_MONTAGE)
    onsets = np.arange(1.0, 61.0)
    raw.set_annotations(mne.Annotations(onsets, 0.0, labels))
    data = raw.get_data()
    frontal = [raw.ch_names.index(x) for x in _TEST_ROIS["frontal"]]
    for onset, label in zip(onsets, labels, strict=True):
        if label == "DEV":
            start = int((onset + 0.3) * raw.info["sfreq"])
            stop = int((onset + 0.5) * raw.info["sfreq"])
            data[frontal, start:stop] += 10e-6
    raw._data[:] = data
    events, _ = mne.events_from_annotations(
        raw, event_id=_EVENT_ID, verbose="error"
    )
    return mne.Epochs(
        raw,
        events,
        _EVENT_ID,
        tmin=-0.2,
        tmax=1.0,
        baseline=(None, 0),
        preload=True,
        verbose="error",
    )


@pytest.fixture(scope="module")
def epochs() -> mne.Epochs:
    """Return epochs with two conditions."""
    return _make_epochs()


def test_read_eeg_files(tmp_path: Path) -> None:
    """Test reading and concatenating the files of a directory."""
    for i, (minute, labels) in enumerate([(10, ["A1", "B1"]), (0, ["A2"])]):
        raw = _block(i, labels)
        stim = mne.create_info([f"STI{i}"], raw.info["sfreq"], "stim")
        raw.add_channels(
            [mne.io.RawArray(np.zeros((1, len(raw.times))), stim)],
            force_update_info=True,
        )
        raw.set_meas_date(datetime(2020, 1, 1, 10, minute, tzinfo=UTC))
        raw.save(tmp_path / f"block{i}_raw.fif", verbose="error")
    with pytest.raises(RuntimeError, match="No EEG files"):
        _read_eeg_files(tmp_path, "*.edf", None, {}, None)
    # The stim channels differ
    with pytest.raises(ValueError, match=r"ch_names.*must match"):
        _read_eeg_files(tmp_path, "*_raw.fif", None, {}, None)
    raw = _read_eeg_files(tmp_path, "*_raw.fif", None, {}, ["stim"])
    assert len(raw.times) == 2 * 5000
    assert "STI0" not in raw.ch_names
    # Sorted by date: block1 first
    descriptions = list(raw.annotations.description)
    assert descriptions.index("A2") < descriptions.index("A1")
    assert "EDGE boundary" in descriptions


def test_rename_events() -> None:
    """Test renaming the events of each block."""
    raw = mne.concatenate_raws(
        [
            _block(0, ["HX", "X", "Y"]),
            _block(1, ["HY", "X", "Y"]),
            _block(2, ["HX", "Y"]),
        ],
        verbose="error",
    )
    rules = [
        {"when": ["HX"], "rename": {"X": "LSGS", "Y": "LDGD"}},
        {"when": ["HY"], "rename": {"X": "LSGD", "Y": "LDGS"}},
    ]
    out = EEGRenameEvents(rules=rules).preprocess(_input(raw))["data"]
    events = [
        x
        for x in out.annotations.description
        if x.startswith("L") or x.startswith("H")
    ]
    assert events == [
        "HX", "LSGS", "LDGD", "HY", "LSGD", "LDGS", "HX", "LDGD",
    ]  # fmt: skip

    # The whole recording: the first rule applies to all the events
    raw = mne.concatenate_raws(
        [_block(0, ["HX", "X"]), _block(1, ["HY", "X"])], verbose="error"
    )
    out = EEGRenameEvents(rules=rules, scope="recording").preprocess(
        _input(raw)
    )["data"]
    assert list(out.annotations.description).count("LSGS") == 2

    # A block without a rule
    raw = mne.concatenate_raws(
        [_block(0, ["HX", "X"]), _block(1, ["X"])], verbose="error"
    )
    with pytest.raises(RuntimeError, match="block 1"):
        EEGRenameEvents(rules=rules).preprocess(_input(raw))
    out = EEGRenameEvents(rules=rules, on_unmatched="ignore").preprocess(
        _input(raw)
    )["data"]
    assert list(out.annotations.description).count("X") == 1


def test_drop_events() -> None:
    """Test dropping the events that follow other events."""
    raw = mne.concatenate_raws(
        [
            _block(0, ["S", "R", "O", "S", "S", "R", "R", "S"]),
            # The first event of a block follows the last of the previous one
            _block(1, ["S", "R", "S"]),
        ],
        verbose="error",
    )
    out = EEGDropEvents(events=["S"], preceded_by=["R"]).preprocess(
        _input(raw)
    )["data"]
    events = [x for x in out.annotations.description if x in {"S", "R", "O"}]
    # The other events (O) are ignored
    assert events == ["S", "R", "O", "S", "R", "R", "S", "R"]
    raw = mne.concatenate_raws(
        [_block(0, ["S", "R"]), _block(1, ["S"])], verbose="error"
    )
    out = EEGDropEvents(
        events=["S"], preceded_by=["R"], scope="recording"
    ).preprocess(_input(raw))["data"]
    assert [x for x in out.annotations.description if x in {"S", "R"}] == [
        "S",
        "R",
    ]


def test_event_epochs() -> None:
    """Test cutting epochs around events, dropping the boundaries."""
    raw = mne.concatenate_raws(
        [_block(0, ["A"] * 19 + ["B"]), _block(1, ["A"] * 19)],
        verbose="error",
    )
    epochs = EEGEventEpochs(
        event_id={"A": 1, "B": 2, "C": 3},
        tmin=-0.2,
        tmax=0.8,
        baseline=[None, 0.0],
    ).preprocess(_input(raw))["data"]
    # B (at 20 s) spans the boundary: dropped
    assert epochs.event_id == {"A": 1, "B": 2}
    assert len(epochs) == 38
    assert len(epochs["A"]) == 38
    assert ("BAD boundary",) in epochs.drop_log
    np.testing.assert_allclose(epochs.times[[0, -1]], [-0.2, 0.8])
    with pytest.raises(RuntimeError, match="None of the events"):
        EEGEventEpochs(event_id={"C": 3}, tmin=-0.2, tmax=0.8).preprocess(
            _input(raw)
        )


def test_cnv_matches_nice(epochs: mne.Epochs) -> None:
    """Test the CNV against NICE."""
    marker = EEGContingentNegativeVariationTimeseries(
        tmin=-0.004,
        tmax=0.596,
        aggregations={"mean": [{"axis": "channels", **_MEAN}]},
    )
    values, features, _ = marker.compute_values(_input(epochs))
    expected, _ = nice.epochs_compute_cnv(epochs, -0.004, 0.596)
    assert features == ["cnv"]
    np.testing.assert_allclose(values[..., 0], expected, rtol=1e-10)
    out = marker.compute(_input(epochs))["mean"]
    assert marker.storage_type(None, "mean") == StorageType.Timeseries
    np.testing.assert_allclose(out["data"][:, 0], expected.mean(axis=1))


def test_erp(epochs: mne.Epochs) -> None:
    """Test the ERP amplitudes in windows."""
    windows = [
        {
            "name": "early",
            "tmin": 0.0,
            "tmax": 0.2,
            "conditions": ["DEV"],
            "picks": _TEST_ROIS["frontal"],
        },
        {
            "name": "late",
            "tmin": 0.3,
            "tmax": 0.5,
            "conditions": ["DEV"],
            "picks": _TEST_ROIS["frontal"],
        },
        # The other conditions and channels
        {
            "name": "std",
            "tmin": 0.3,
            "tmax": 0.5,
            "conditions": ["STD"],
            "picks": ["Cz", "Pz"],
        },
    ]
    aggregations = {
        "mean": [
            {"axis": "epochs", **_MEAN},
            {"axis": "channels", **_MEAN},
            {"axis": "times", **_MEAN},
        ]
    }
    marker = EEGEventRelatedPotentialScalar(
        windows=windows, aggregations=aggregations
    )
    out = marker.compute(_input(epochs))["mean"]
    assert out["col_names"] == ["early", "late", "std"]
    for value, window in zip(out["data"], windows, strict=True):
        data = epochs[window["conditions"][0]].get_data(picks=window["picks"])
        mask = (epochs.times >= window["tmin"]) & (
            epochs.times <= window["tmax"]
        )
        np.testing.assert_allclose(value, data[..., mask].mean())
    # The deviant response
    assert out["data"][1] > out["data"][0] + 5e-6
    # The picks are set by the windows
    with pytest.raises(ValueError, match="set by the windows"):
        EEGEventRelatedPotentialScalar(
            windows=windows,
            aggregations={
                "mean": [
                    {"axis": "epochs", **_MEAN},
                    {"axis": "channels", "picks": "frontal", **_MEAN},
                    {"axis": "times", **_MEAN},
                ]
            },
        )

    topo = EEGEventRelatedPotentialTopography(
        windows=windows,
        aggregations={
            "mean": [{"axis": "epochs", **_MEAN}, {"axis": "times", **_MEAN}]
        },
    ).compute(_input(epochs))["mean"]
    assert topo["data"].shape == (len(epochs.ch_names), 3)
    assert topo["row_names"] == epochs.ch_names


def test_contrast(epochs: mne.Epochs) -> None:
    """Test the contrasts, with the channels of each contrast."""
    contrasts = [
        {
            "name": "late",
            "condition_a": ["DEV"],
            "condition_b": ["STD"],
            "tmin": 0.3,
            "tmax": 0.5,
            "picks": "frontal",
        },
        {"name": "all", "condition_a": ["DEV"], "condition_b": ["STD"]},
    ]
    aggregations = {
        "mean": [
            {"axis": "epochs", **_MEAN},
            {"axis": "channels", **_MEAN},
            {"axis": "times", **_MEAN},
        ]
    }
    marker = EEGEventRelatedContrastScalar(
        contrasts=contrasts, aggregations=aggregations
    )
    out = marker.compute(_input(epochs))["mean"]
    assert out["col_names"] == ["late", "all"]
    frontal = mne.pick_channels(epochs.ch_names, _TEST_ROIS["frontal"])
    mask = (epochs.times >= 0.3) & (epochs.times <= 0.5)
    dev = epochs["DEV"].get_data()
    std = epochs["STD"].get_data()
    expected = [
        dev[:, frontal][..., mask].mean() - std[:, frontal][..., mask].mean(),
        dev.mean() - std.mean(),
    ]
    np.testing.assert_allclose(out["data"], expected)
    assert out["data"][0] == pytest.approx(10e-6, rel=0.1)

    topo = EEGEventRelatedContrastTopography(
        contrasts=contrasts,
        aggregations={
            "mean": [{"axis": "epochs", **_MEAN}, {"axis": "times", **_MEAN}]
        },
    ).compute(_input(epochs))["mean"]
    assert topo["data"].shape == (len(epochs.ch_names), 2)

    # The channels step cannot set picks when the contrasts do
    with pytest.raises(ValueError, match="set by the contrasts"):
        EEGEventRelatedContrastScalar(
            contrasts=contrasts,
            aggregations={
                "mean": [
                    {"axis": "epochs", **_MEAN},
                    {"axis": "channels", "picks": "scalp", **_MEAN},
                    {"axis": "times", **_MEAN},
                ]
            },
        )
    with pytest.raises(ValueError, match="No epochs"):
        EEGEventRelatedContrastScalar(
            contrasts=[{**contrasts[1], "condition_a": ["XXX"]}],
            aggregations=aggregations,
        ).compute(_input(epochs))


def test_window_decoding(epochs: mne.Epochs) -> None:
    """Test the window decoding."""
    decoders = [
        {
            "name": "late",
            "condition_a": ["DEV"],
            "condition_b": ["STD"],
            "tmin": 0.3,
            "tmax": 0.5,
        },
        {
            "name": "baseline",
            "condition_a": ["DEV"],
            "condition_b": ["STD"],
            "tmin": -0.2,
            "tmax": 0.0,
        },
    ]
    aggregations = {"mean": [{"axis": "folds", **_MEAN}]}
    marker = EEGWindowDecodingScalar(
        decoders=decoders, n_splits=5, seed=1, aggregations=aggregations
    )
    values, features, _ = marker.compute_values(_input(epochs))
    assert features == ["late", "baseline"]
    assert values[0].shape == (5, 1)
    out = marker.compute(_input(epochs))["mean"]
    # Same seed, same folds
    np.testing.assert_array_equal(out["data"], [x.mean() for x in values])
    late, baseline = out["data"]
    assert late > 0.9
    assert 0.2 < baseline < 0.8


@pytest.mark.parametrize(
    "klass, aggregations, match",
    [
        (
            EEGWindowDecodingScalar,
            {"x": [{"axis": "epochs", **_MEAN}]},
            "missing",
        ),
        (
            EEGContingentNegativeVariationScalar,
            {"x": [{"axis": "times", **_MEAN}]},
            "not allowed",
        ),
        (
            EEGEventRelatedPotentialScalar,
            {
                "x": [
                    {"axis": "epochs", **_MEAN},
                    {"axis": "channels", **_MEAN},
                    {"axis": "times", "picks": "scalp", **_MEAN},
                ]
            },
            "only valid for the channels",
        ),
    ],
)
def test_axes_validation(klass: type, aggregations: dict, match: str) -> None:
    """Test the validation of the axes of the aggregations."""
    params = {
        EEGWindowDecodingScalar: {
            "decoders": [
                {"name": "x", "condition_a": ["A"], "condition_b": ["B"]}
            ]
        },
        EEGContingentNegativeVariationScalar: {},
        EEGEventRelatedPotentialScalar: {"windows": [{"name": "x"}]},
    }[klass]
    with pytest.raises(ValueError, match=match):
        klass(aggregations=aggregations, **params)
