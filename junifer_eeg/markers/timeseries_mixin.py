"""Provide mixin for the markers reduced to one value per epoch."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import numpy as np
from junifer.storage import StorageType
from junifer.typing import MarkerInOutMappings

from ..datatypes import EEG
from .aggregation import Axis


__all__ = ["TimeseriesMixin"]


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
