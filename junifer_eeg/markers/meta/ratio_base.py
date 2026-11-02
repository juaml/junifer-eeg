"""Provide base class for the ratio markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from typing import Any, ClassVar

import numpy as np
from junifer.utils import raise_error

from ..aggregation import Axis
from ..base import EEGBaseMarker
from ..scalar_mixin import ScalarMixin
from ..timeseries_mixin import TimeseriesMixin
from ..topography_mixin import TopographyMixin
from .ratio import Ratio
from .ratio_operand import RatioOperand


__all__ = ["EEGRatio"]


def _make_operand_marker(operand: RatioOperand) -> EEGBaseMarker:
    """Make the marker computing the values of an operand.

    Parameters
    ----------
    operand : RatioOperand
        The operand.

    Returns
    -------
    EEGBaseMarker
        The marker. Only its ``compute_values`` is used.

    Raises
    ------
    ValueError
        If the marker is not a base marker with the ``epochs`` and
        ``channels`` axes.

    """
    from ... import markers  # imported lazily (import cycle)

    klass = getattr(markers, operand.marker, None)
    kinds = (ScalarMixin, TopographyMixin, TimeseriesMixin)
    if (
        not isinstance(klass, type)
        or not issubclass(klass, EEGBaseMarker)
        or issubclass(klass, kinds)
        or klass is EEGBaseMarker
    ):
        raise_error(
            f"Unknown marker {operand.marker}: it must be the base class of a "
            "marker (e.g., EEGPowerSpectralDensity, not its Scalar kind)"
        )
    if klass._AXES != EEGRatio._AXES:
        raise_error(
            f"The values of {operand.marker} have the axes "
            f"{list(klass._AXES)}, a ratio needs {list(EEGRatio._AXES)}"
        )
    # A kind is needed to instantiate the marker: its aggregation (one step
    # per axis) is not used
    values_klass = type(f"_{klass.__name__}Values", (ScalarMixin, klass), {})
    return values_klass(
        **operand.params,
        aggregations={
            "values": [{"axis": x, "method": "mean"} for x in klass._AXES]
        },
    )


class EEGRatio(EEGBaseMarker):
    """Base class for the ratio markers.

    For each ratio (a feature), the values of a feature of the numerator
    marker are divided by the values of a feature of the denominator marker,
    for each epoch and channel (e.g., the theta over the alpha power). The
    markers are computed with their parameters (the shared estimators are
    cached, e.g., the PSD). Port of ``nice_sandbox.markers.Ratio``.

    Parameters
    ----------
    ratios : list of Ratio
        The ratios.
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _AXES: ClassVar[tuple[Axis, ...]] = ("epochs", "channels")

    ratios: list[Ratio]

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        if len(self.ratios) == 0:
            raise_error("At least one ratio is needed")
        names = [x.name for x in self.ratios]
        if len(set(names)) != len(names):
            raise_error(f"The names of the ratios must be unique: {names}")
        for ratio in self.ratios:
            for operand in (ratio.numerator, ratio.denominator):
                _make_operand_marker(operand)

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Compute the ratios.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        numpy.ndarray
            The values, shape (n_epochs, n_channels, n_ratios).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        values = []
        ch_names = None
        for ratio in self.ratios:
            operands = []
            for operand in (ratio.numerator, ratio.denominator):
                marker = _make_operand_marker(operand)
                data, features, this_ch_names = marker.compute_values(input)
                if operand.feature not in features:
                    raise_error(
                        f"Ratio {ratio.name}: {operand.marker} has no feature "
                        f"{operand.feature} (features: {features})"
                    )
                if ch_names is None:
                    ch_names = this_ch_names
                elif this_ch_names != ch_names:
                    raise_error(
                        f"Ratio {ratio.name}: the markers have different "
                        "channels"
                    )
                idx = features.index(operand.feature)
                if isinstance(data, list):
                    data = data[idx]
                    idx = 0
                operands.append(data[..., idx])
            values.append(operands[0] / operands[1])
        return (
            np.stack(values, axis=-1),
            [x.name for x in self.ratios],
            ch_names,
        )
