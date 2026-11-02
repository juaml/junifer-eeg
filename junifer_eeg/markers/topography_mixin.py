"""Provide mixin for the markers reduced to topographies."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import numpy as np
from junifer.storage import StorageType
from junifer.typing import MarkerInOutMappings

from ..datatypes import EEG
from .aggregation import Axis


__all__ = ["TopographyMixin"]


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
