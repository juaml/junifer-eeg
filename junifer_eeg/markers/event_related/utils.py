"""Provide utilities for the event-related markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any

import mne
import numpy as np
from junifer.utils import raise_error

from ..aggregation import AggregationStep
from ..utils import get_picks, time_mask
from .window import Window


__all__ = ["check_feature_picks", "get_window_data"]


def get_window_data(
    epochs: mne.BaseEpochs,
    conditions: list[str] | None,
    tmin: float | None,
    tmax: float | None,
) -> tuple[np.ndarray, list[str]]:
    """Get the data of the epochs of some conditions in a time window.

    Parameters
    ----------
    epochs : mne.BaseEpochs
        The epochs.
    conditions : list of str or None
        The conditions (event names) of the epochs to use. If None, all the
        epochs are used.
    tmin : float or None
        The start of the window. If None, from the start.
    tmax : float or None
        The end of the window (included). If None, until the end.

    Returns
    -------
    numpy.ndarray
        The data, shape (n_epochs, n_channels, n_times).
    list of str
        The names of the channels.

    Raises
    ------
    ValueError
        If there are no epochs of the conditions.

    """
    if conditions is not None:
        missing = [x for x in conditions if x not in epochs.event_id]
        if len(missing) == len(conditions):
            raise_error(
                f"No epochs of the conditions {conditions} (the conditions "
                f"are {list(epochs.event_id)})"
            )
        epochs = epochs[[x for x in conditions if x not in missing]]
    picks = get_picks(epochs.info)
    mask = time_mask(epochs.times, tmin, tmax)
    data = epochs.get_data(picks=picks)[..., mask]
    return data, [epochs.ch_names[x] for x in picks]


def check_feature_picks(
    aggregations: dict[str, list[AggregationStep]],
    items: list[Window] | list[Any],
    kind: str,
) -> None:
    """Check the names and the picks of the features of a marker.

    Parameters
    ----------
    aggregations : dict of str and list of AggregationStep
        The aggregations of the marker.
    items : list
        The features (e.g., windows or contrasts), with a ``name`` and
        ``picks``.
    kind : str
        The kind of feature, for the error messages (e.g., "windows").

    Raises
    ------
    ValueError
        If there are no features, the names are repeated, or a ``channels``
        step sets its picks while a feature sets them.

    """
    if len(items) == 0:
        raise_error(f"At least one of the {kind} is needed")
    names = [x.name for x in items]
    if len(set(names)) != len(names):
        raise_error(f"The names of the {kind} must be unique: {names}")
    if any(x.picks is not None for x in items):
        for agg_name, steps in aggregations.items():
            if any(
                x.axis == "channels" and x.picks is not None for x in steps
            ):
                raise_error(
                    f"Aggregation {agg_name}: the `channels` step cannot "
                    f"set `picks`, they are set by the {kind}"
                )
