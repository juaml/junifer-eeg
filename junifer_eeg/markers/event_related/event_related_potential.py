"""Provide the event-related potential (ERP) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar

import mne
import numpy as np
from junifer.api.decorators import register_marker
from junifer.utils import raise_error
from pydantic import BaseModel, ConfigDict

from ..aggregation import AggregationStep, Axis
from ..base import EEGBaseMarker, ScalarMixin, TopographyMixin
from ..utils import get_epochs, get_picks, time_mask


__all__ = [
    "EEGEventRelatedPotential",
    "EEGEventRelatedPotentialScalar",
    "EEGEventRelatedPotentialTopography",
    "Window",
    "check_feature_picks",
    "get_window_data",
]


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


class Window(BaseModel):
    """A time window of the epochs of some conditions.

    Parameters
    ----------
    name : str
        The name of the window (the feature).
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).
    conditions : list of str or None, optional
        The conditions (event names) of the epochs to use. If None, all the
        epochs are used (default None).
    picks : str or list of str or None, optional
        The channels reduced by the ``channels`` aggregation step, as names
        of ROIs or channels (see :class:`.AggregationStep`). If None, the
        picks of the step (default None).

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    tmin: float | None = None
    tmax: float | None = None
    conditions: list[str] | None = None
    picks: str | list[str] | None = None


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


class EEGEventRelatedPotential(EEGBaseMarker):
    """Base class for the event-related potential (ERP) markers.

    The values are the amplitudes of the epochs of each window (a feature),
    for each channel and sample. Port of ``nice.markers.TimeLockedTopography``.

    Parameters
    ----------
    windows : list of Window
        The windows.
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`. A
        ``channels`` step cannot set its picks if a window sets them.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _AXES: ClassVar[tuple[Axis, ...]] = ("epochs", "channels", "times")

    windows: list[Window]

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        check_feature_picks(self.aggregations, self.windows, "windows")

    def compute(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.
        extra_input : dict, optional
            The other fields in the data object (default None).

        Returns
        -------
        dict
            The output of each aggregation, as a dictionary with the keys
            needed by the storage type.

        """
        epochs = get_epochs(input)
        features = [x.name for x in self.windows]
        # The amplitudes of each window
        values = []
        for window in self.windows:
            data, ch_names = get_window_data(
                epochs, window.conditions, window.tmin, window.tmax
            )
            values.append(data[..., np.newaxis])
        out = {}
        for agg_name, steps in self.aggregations.items():
            # Only the channels reduced by the aggregation are picked
            data = np.concatenate(
                [
                    self._aggregate(
                        x, steps, input, ch_names, channel_picks=window.picks
                    )
                    for window, x in zip(self.windows, values, strict=True)
                ],
                axis=-1,
            )
            out[agg_name] = self._format_output(data, features, ch_names)
        return out


@register_marker
class EEGEventRelatedPotentialScalar(ScalarMixin, EEGEventRelatedPotential):
    """Class for the ERP markers, reduced to scalars.

    See :class:`.EEGEventRelatedPotential` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGEventRelatedPotentialTopography(
    TopographyMixin, EEGEventRelatedPotential
):
    """Class for the ERP markers, reduced to topographies.

    See :class:`.EEGEventRelatedPotential` and :class:`.TopographyMixin`.

    """
