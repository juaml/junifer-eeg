"""Provide the event-related contrast markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar

import numpy as np
from junifer.api.decorators import register_marker
from pydantic import BaseModel, ConfigDict

from ..aggregation import Axis
from ..base import EEGBaseMarker, ScalarMixin, TopographyMixin
from ..utils import get_epochs
from .event_related_potential import check_feature_picks, get_window_data


__all__ = [
    "Contrast",
    "EEGEventRelatedContrast",
    "EEGEventRelatedContrastScalar",
    "EEGEventRelatedContrastTopography",
]


class Contrast(BaseModel):
    """A contrast between the epochs of two sets of conditions.

    Parameters
    ----------
    name : str
        The name of the contrast (the feature).
    condition_a : list of str
        The conditions (event names) of the epochs of the first set.
    condition_b : list of str
        The conditions (event names) of the epochs of the second set.
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).
    picks : str or list of str or None, optional
        The channels reduced by the ``channels`` aggregation step, as an ROI
        name or a list of channel names. If None, the picks of the step
        (default None).

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    condition_a: list[str]
    condition_b: list[str]
    tmin: float | None = None
    tmax: float | None = None
    picks: str | list[str] | None = None


class EEGEventRelatedContrast(EEGBaseMarker):
    """Base class for the event-related contrast markers.

    For each contrast (a feature), the amplitudes of the epochs of
    ``condition_a`` and of ``condition_b`` in the window are aggregated
    separately, and the contrast is the difference (a minus b). Port of
    ``nice.markers.TimeLockedContrast``.

    The ``epochs`` axis is always reduced (the two sets of epochs differ), so
    there is no timeseries kind.

    Parameters
    ----------
    contrasts : list of Contrast
        The contrasts.
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`. A
        ``channels`` step cannot set its picks if a contrast sets them.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _AXES: ClassVar[tuple[Axis, ...]] = ("epochs", "channels", "times")

    contrasts: list[Contrast]

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        check_feature_picks(self.aggregations, self.contrasts, "contrasts")

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
        features = [x.name for x in self.contrasts]
        out = {}
        # The amplitudes of each set of epochs, for each contrast
        values = []
        for contrast in self.contrasts:
            data_a, ch_names = get_window_data(
                epochs, contrast.condition_a, contrast.tmin, contrast.tmax
            )
            data_b, _ = get_window_data(
                epochs, contrast.condition_b, contrast.tmin, contrast.tmax
            )
            values.append((data_a[..., np.newaxis], data_b[..., np.newaxis]))
        for agg_name, steps in self.aggregations.items():
            data = []
            for contrast, (data_a, data_b) in zip(
                self.contrasts, values, strict=True
            ):
                # Only the channels reduced by the aggregation are picked
                reduced_a, reduced_b = (
                    self._aggregate(
                        x, steps, input, ch_names, channel_picks=contrast.picks
                    )
                    for x in (data_a, data_b)
                )
                data.append(reduced_a - reduced_b)
            data = np.concatenate(data, axis=-1)
            out[agg_name] = self._format_output(data, features, ch_names)
        return out


@register_marker
class EEGEventRelatedContrastScalar(ScalarMixin, EEGEventRelatedContrast):
    """Class for the event-related contrast markers, reduced to scalars.

    See :class:`.EEGEventRelatedContrast` and :class:`.ScalarMixin`.

    """


@register_marker
class EEGEventRelatedContrastTopography(
    TopographyMixin, EEGEventRelatedContrast
):
    """Class for the event-related contrast markers, reduced to topographies.

    See :class:`.EEGEventRelatedContrast` and :class:`.TopographyMixin`.

    """
