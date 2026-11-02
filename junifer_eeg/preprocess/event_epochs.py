"""Provide class for cutting continuous EEG data into epochs around events."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar

import mne
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error

from .base import EEGBasePreprocessor


__all__ = ["EEGEventEpochs"]


@register_preprocessor
class EEGEventEpochs(EEGBasePreprocessor):
    """Class for cutting continuous EEG data into epochs around events.

    The events are the annotations with the names in ``event_id``. The events
    that are not present are ignored.

    Parameters
    ----------
    event_id : dict of str and int
        The name and code of each event.
    tmin : float
        The start of each epoch relative to its event, in seconds.
    tmax : float
        The end of each epoch relative to its event, in seconds (included).
    baseline : list of float or None, optional
        The baseline interval. See :class:`mne.Epochs` (default None).
    reject_by_annotation : bool, optional
        Whether to drop the epochs that overlap the annotations starting with
        "bad" (e.g., the boundaries of concatenated files) (default True).

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    event_id: dict[str, int]
    tmin: float
    tmax: float
    baseline: list[float | None] | None = None
    reject_by_annotation: bool = True

    def validate_preprocessor_params(self) -> None:
        """Run extra logical validation for the preprocessor."""
        if self.tmin >= self.tmax:
            raise_error("`tmin` must be less than `tmax`")

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        present = set(inst.annotations.description)
        event_id = {k: v for k, v in self.event_id.items() if k in present}
        if len(event_id) == 0:
            raise_error(
                f"None of the events {list(self.event_id)} are in the data",
                klass=RuntimeError,
            )
        events, _ = mne.events_from_annotations(
            inst, event_id=event_id, verbose="error"
        )
        baseline = None if self.baseline is None else tuple(self.baseline)
        return mne.Epochs(
            inst,
            events,
            event_id=event_id,
            tmin=self.tmin,
            tmax=self.tmax,
            baseline=baseline,
            reject=None,
            reject_by_annotation=self.reject_by_annotation,
            preload=True,
            verbose="error",
        )
