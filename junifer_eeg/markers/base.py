"""Provide the base classes for EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections import Counter
from typing import Any, ClassVar

import numpy as np
from junifer.datagrabber import DataType
from junifer.markers import BaseMarker
from junifer.storage import StorageType
from junifer.typing import Dependencies, MarkerInOutMappings
from junifer.utils import raise_error

from ..data import get_roi_channels
from ..datatypes import EEG
from .aggregation import AggregationStep, Axis, get_aggregation_function


__all__ = [
    "EEGBaseMarker",
    "ScalarMixin",
    "TimeseriesMixin",
    "TopographyMixin",
]


class EEGBaseMarker(BaseMarker):
    """Base class for EEG markers.

    A marker computes its values along its axes (``_AXES``, e.g., for each
    epoch and channel), for one or more features (e.g., the power in each
    frequency band). The values are then reduced with each of the
    ``aggregations``, to the dimensionality set by the kind of marker (see
    :class:`ScalarMixin`, :class:`TopographyMixin` and
    :class:`TimeseriesMixin`). Each aggregation is stored as a feature of the
    marker (``<name>_<aggregation>``).

    The base classes of the markers compute the values and cannot be used
    directly: the concrete markers combine them with one of the mixins.

    Parameters
    ----------
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute: a name and the list of steps, one for
        each axis to reduce. The axes are reduced in the order of the steps
        (e.g., first across epochs and then across channels, as in Sitt et
        al. 2014). The order matters unless all the steps are means.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker. If None, will use the class name
        (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"mne", "numpy", "junifer_eeg"}
    # The axes of the values, before the features
    _AXES: ClassVar[tuple[Axis, ...]] = ("epochs", "channels")
    # Set by the mixins
    _KEPT_AXES: ClassVar[tuple[Axis, ...]]
    _STORAGE_TYPE: ClassVar[StorageType]

    aggregations: dict[str, list[AggregationStep]]

    @classmethod
    def _reduced_axes(cls) -> list[Axis]:
        """Get the axes that each aggregation must reduce."""
        return [x for x in cls._AXES if x not in cls._KEPT_AXES]

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        not_kept = [x for x in self._KEPT_AXES if x not in self._AXES]
        if not_kept:
            raise_error(
                f"{self.__class__.__name__} cannot keep the axes {not_kept}, "
                f"its axes are {list(self._AXES)}"
            )
        if len(self.aggregations) == 0:
            raise_error("At least one aggregation is needed")
        required = self._reduced_axes()
        for agg_name, steps in self.aggregations.items():
            counts = Counter(step.axis for step in steps)
            missing = [x for x in required if counts[x] == 0]
            extra = [x for x in counts if x not in required]
            repeated = [x for x, n in counts.items() if n > 1]
            if missing or extra or repeated:
                raise_error(
                    f"Aggregation {agg_name} of {self.__class__.__name__} "
                    f"must have one step for each of the axes {required} "
                    f"(missing: {missing}, not allowed: {extra}, repeated: "
                    f"{repeated})"
                )
            for step in steps:
                # Check the function exists
                get_aggregation_function(step.method, step.method_params)
                if step.picks is not None and step.axis not in (
                    "channels",
                    "channels_y",
                ):
                    raise_error(
                        f"Aggregation {agg_name}: `picks` is only valid for "
                        "the channels"
                    )

    def storage_type(
        self, input_type: DataType, output_feature: str
    ) -> StorageType:
        """Get :enum:`junifer.storage.StorageType` for a feature.

        All the features (aggregations) of a marker have the same storage
        type, set by its kind.

        Parameters
        ----------
        input_type : :enum:`junifer.datagrabber.DataType`
            The data type input to the marker.
        output_feature : str
            The feature output of the marker.

        Returns
        -------
        :enum:`junifer.storage.StorageType`
            The storage type output of the marker.

        """
        return self._STORAGE_TYPE

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray | list[np.ndarray], list[str], list[str]]:
        """Compute the values of the marker.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray or list of numpy.ndarray
            The values, shape ``(*axes, n_features)``, with the axes of the
            marker (``_AXES``). If the features have different shapes (e.g.,
            different time windows), a list with the values of each feature,
            each of shape ``(*axes, 1)``.
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        raise_error(
            msg="Concrete classes need to implement compute_values().",
            klass=NotImplementedError,
        )

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
        values, features, ch_names = self.compute_values(input)
        if not isinstance(values, list):
            values = [values]
        out = {}
        for agg_name, steps in self.aggregations.items():
            data = np.concatenate(
                [self._aggregate(x, steps, input, ch_names) for x in values],
                axis=-1,
            )
            out[agg_name] = self._format_output(data, features, ch_names)
        return out

    def _aggregate(
        self,
        values: np.ndarray,
        steps: list[AggregationStep],
        input: dict[str, Any],
        ch_names: list[str],
        channel_picks: str | list[str] | None = None,
    ) -> np.ndarray:
        """Reduce the values with the steps of an aggregation.

        Parameters
        ----------
        values : numpy.ndarray
            The values, shape ``(*axes, n_features)``.
        steps : list of AggregationStep
            The steps of the aggregation.
        input : dict
            The ``EEG`` item of the data object, with the ``montage``.
        ch_names : list of str
            The names of the channels of the values.
        channel_picks : str or list of str or None, optional
            The channels to aggregate in the ``channels`` step, instead of
            the picks of the step (default None).

        Returns
        -------
        numpy.ndarray
            The reduced values, shape (*kept axes, n_features).

        """
        data = values
        t_axes = [*self._AXES, "features"]
        for step in steps:
            idx = t_axes.index(step.axis)
            picks = step.picks
            if step.axis == "channels" and channel_picks is not None:
                picks = channel_picks
            if picks is not None:
                indices = _get_channel_indices(picks, input, ch_names)
                data = np.take(data, indices, axis=idx)
            func = get_aggregation_function(step.method, step.method_params)
            data = np.asarray(func(data, axis=idx))
            t_axes.pop(idx)
        return data

    def _format_output(
        self, data: np.ndarray, features: list[str], ch_names: list[str]
    ) -> dict[str, Any]:
        """Format the output of an aggregation for the storage.

        Set by the mixins.

        """
        raise_error(
            msg="Concrete classes need a mixin to set the output.",
            klass=NotImplementedError,
        )


def _get_channel_indices(
    picks: str | list[str], input: dict[str, Any], ch_names: list[str]
) -> list[int]:
    """Get the indices of a channel selection.

    Parameters
    ----------
    picks : str or list of str
        The name of an ROI or the list of channel names.
    input : dict
        The ``EEG`` item of the data object, with the ``montage``.
    ch_names : list of str
        The names of the channels of the marker values.

    Returns
    -------
    list of int
        The indices of the channels.

    Raises
    ------
    ValueError
        If some channels of the list are not in the data, or no channel of
        the ROI.

    """
    names = get_roi_channels(picks, input, ch_names)
    missing = [x for x in names if x not in ch_names]
    if missing:
        raise_error(f"Channels of {picks} not in the data: {missing}")
    return [ch_names.index(x) for x in names]


class ScalarMixin:
    """Mixin for markers reduced to one value for each feature.

    Each aggregation reduces all the axes of the marker, and is stored as a
    vector with one column for each feature.

    """

    _KEPT_AXES: ClassVar[tuple[Axis, ...]] = ()
    _STORAGE_TYPE: ClassVar[StorageType] = StorageType.Vector
    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        EEG: {"scalar": StorageType.Vector},
    }

    def _format_output(
        self, data: np.ndarray, features: list[str], ch_names: list[str]
    ) -> dict[str, Any]:
        return {"data": data, "col_names": features}


class TopographyMixin:
    """Mixin for markers reduced to one value for each channel and feature.

    Each aggregation reduces all the axes of the marker but the channels, and
    is stored as a scalar table with one row for each channel and one column
    for each feature.

    """

    _KEPT_AXES: ClassVar[tuple[Axis, ...]] = ("channels",)
    _STORAGE_TYPE: ClassVar[StorageType] = StorageType.ScalarTable
    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        EEG: {"topography": StorageType.ScalarTable},
    }

    def _format_output(
        self, data: np.ndarray, features: list[str], ch_names: list[str]
    ) -> dict[str, Any]:
        return {
            "data": data,
            "col_names": features,
            "row_names": ch_names,
            "row_header_col_name": "channel",
        }


class TimeseriesMixin:
    """Mixin for markers reduced to one value for each epoch and feature.

    Each aggregation reduces all the axes of the marker but the epochs, and
    is stored as a timeseries with one row for each epoch and one column for
    each feature.

    """

    _KEPT_AXES: ClassVar[tuple[Axis, ...]] = ("epochs",)
    _STORAGE_TYPE: ClassVar[StorageType] = StorageType.Timeseries
    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        EEG: {"timeseries": StorageType.Timeseries},
    }

    def _format_output(
        self, data: np.ndarray, features: list[str], ch_names: list[str]
    ) -> dict[str, Any]:
        return {"data": data, "col_names": features}
