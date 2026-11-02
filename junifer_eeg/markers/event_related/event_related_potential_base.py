"""Provide base class for the event-related potential (ERP) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar

import numpy as np

from ..aggregation import Axis
from ..base import EEGBaseMarker
from ..utils import get_epochs
from .utils import check_feature_picks, get_window_data
from .window import Window


__all__ = ["EEGEventRelatedPotential"]


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
