"""Provide class for dropping the events that follow other events."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Literal

import mne
import numpy as np
import structlog
from junifer.api.decorators import register_preprocessor

from ._events import _get_blocks, _set_descriptions
from .base import EEGBasePreprocessor


__all__ = ["EEGDropEvents"]


_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="preprocess", step="preprocess")


@register_preprocessor
class EEGDropEvents(EEGBasePreprocessor):
    """Class for dropping the events (annotations) that follow other events.

    Drops each of the ``events`` whose previous event, among the ``events``
    and the ``preceded_by`` events, is one of the ``preceded_by`` events
    (e.g., the frequent trials right after a rare trial). The other
    annotations are ignored. With ``scope="block"``, the first event of each
    block (between the boundaries of the concatenated files) is never
    dropped.

    Parameters
    ----------
    events : list of str
        The events to drop.
    preceded_by : list of str
        The events after which the ``events`` are dropped.
    scope : {"block", "recording"}, optional
        Whether the previous event is searched in the block or in the whole
        recording (default "block").

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    events: list[str]
    preceded_by: list[str]
    scope: Literal["block", "recording"] = "block"

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        descriptions = np.array(inst.annotations.description, dtype=object)
        blocks, _ = _get_blocks(inst.annotations, self.scope)
        is_event = np.isin(descriptions, self.events)
        # The events considered, in order (annotations are sorted by onset)
        considered = np.flatnonzero(
            is_event | np.isin(descriptions, self.preceded_by)
        )
        previous, current = considered[:-1], considered[1:]
        drop = (
            is_event[current]
            & ~is_event[previous]
            & (blocks[current] == blocks[previous])
        )
        keep = np.ones(len(descriptions), dtype=bool)
        keep[current[drop]] = False
        logger.info(f"Dropping {drop.sum()} events after {self.preceded_by}")
        _set_descriptions(inst, descriptions, keep)
        return inst
