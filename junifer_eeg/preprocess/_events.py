"""Provide utilities for the events (annotations) of the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Literal

import mne
import numpy as np


# The annotation that MNE adds between concatenated files
_BOUNDARY = "EDGE boundary"


def _get_blocks(
    annotations: mne.Annotations, scope: Literal["block", "recording"]
) -> tuple[np.ndarray, int]:
    """Get the block of each annotation.

    Parameters
    ----------
    annotations : mne.Annotations
        The annotations.
    scope : {"block", "recording"}
        Whether to split the recording in blocks (at the boundaries of the
        concatenated files) or to keep it as a single block.

    Returns
    -------
    numpy.ndarray
        The index of the block of each annotation.
    int
        The number of blocks.

    """
    onsets = annotations.onset
    if scope == "recording":
        return np.zeros(len(onsets), dtype=int), 1
    descriptions = np.asarray(annotations.description)
    edges = np.sort(onsets[descriptions == _BOUNDARY])
    # A boundary starts a block
    return np.searchsorted(edges, onsets, side="right"), len(edges) + 1


def _set_descriptions(
    inst: mne.io.BaseRaw, descriptions: np.ndarray, keep: np.ndarray
) -> None:
    """Replace the annotations with new descriptions.

    Parameters
    ----------
    inst : mne.io.BaseRaw
        The continuous data.
    descriptions : numpy.ndarray
        The description of each annotation.
    keep : numpy.ndarray
        Whether to keep each annotation.

    """
    annotations = inst.annotations
    inst.set_annotations(
        mne.Annotations(
            onset=annotations.onset[keep],
            duration=annotations.duration[keep],
            description=descriptions[keep].astype(str),
            orig_time=annotations.orig_time,
            ch_names=[
                x for x, k in zip(annotations.ch_names, keep, strict=True) if k
            ],
        )
    )
