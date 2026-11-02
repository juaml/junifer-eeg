"""Provide mixin for the markers reduced to scalars."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import numpy as np
from junifer.storage import StorageType
from junifer.typing import MarkerInOutMappings

from ..datatypes import EEG
from .aggregation import Axis


__all__ = ["ScalarMixin"]


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
