"""Provide preprocessors for the events of the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Literal

import mne
import numpy as np
import structlog
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error
from pydantic import BaseModel, ConfigDict

from .base import EEGBasePreprocessor


__all__ = ["EEGDropEvents", "EEGRenameEvents", "RenameRule"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="preprocess", step="preprocess")

# The annotation that MNE adds between concatenated files
_BOUNDARY = "EDGE boundary"


def _get_blocks(
    annotations: mne.Annotations, scope: Literal["block", "recording"]
) -> tuple[np.ndarray, int]:
    """Get the block of each annotation.

    Parameters
    ----------
    annotations : mne.Annotations
        The annotations.
    scope : {"block", "recording"}
        Whether to split the recording in blocks (at the boundaries of the
        concatenated files) or to keep it as a single block.

    Returns
    -------
    numpy.ndarray
        The index of the block of each annotation.
    int
        The number of blocks.

    """
    onsets = annotations.onset
    if scope == "recording":
        return np.zeros(len(onsets), dtype=int), 1
    descriptions = np.asarray(annotations.description)
    edges = np.sort(onsets[descriptions == _BOUNDARY])
    # A boundary starts a block
    return np.searchsorted(edges, onsets, side="right"), len(edges) + 1


def _set_descriptions(
    inst: mne.io.BaseRaw, descriptions: np.ndarray, keep: np.ndarray
) -> None:
    """Replace the annotations with new descriptions.

    Parameters
    ----------
    inst : mne.io.BaseRaw
        The continuous data.
    descriptions : numpy.ndarray
        The description of each annotation.
    keep : numpy.ndarray
        Whether to keep each annotation.

    """
    annotations = inst.annotations
    inst.set_annotations(
        mne.Annotations(
            onset=annotations.onset[keep],
            duration=annotations.duration[keep],
            description=descriptions[keep].astype(str),
            orig_time=annotations.orig_time,
            ch_names=[
                x for x, k in zip(annotations.ch_names, keep, strict=True) if k
            ],
        )
    )


class RenameRule(BaseModel):
    """A rule for renaming the events (annotations).

    Parameters
    ----------
    when : list of str or None, optional
        The rule applies if any of these events is present. If None, the rule
        always applies (default None).
    rename : dict of str and str
        The new name of each event. The other events are kept.

    """

    model_config = ConfigDict(extra="forbid")

    when: list[str] | None = None
    rename: dict[str, str]


@register_preprocessor
class EEGRenameEvents(EEGBasePreprocessor):
    """Class for renaming the events (annotations) of continuous EEG data.

    The first of the ``rules`` that applies renames the events. With
    ``scope="block"``, the rules are applied to each block of the recording
    (between the boundaries of the concatenated files), so the events of each
    block can be renamed differently (e.g., depending on the condition of
    the block).

    Parameters
    ----------
    rules : list of RenameRule
        The rules, in order of precedence.
    scope : {"block", "recording"}, optional
        Whether to apply the rules to each block or to the whole recording
        (default "block").
    on_unmatched : {"raise", "warn", "ignore"}, optional
        What to do if no rule applies to a block (default "raise").

    """

    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.io.BaseRaw,)

    rules: list[RenameRule]
    scope: Literal["block", "recording"] = "block"
    on_unmatched: Literal["raise", "warn", "ignore"] = "raise"

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        descriptions = np.array(inst.annotations.description, dtype=object)
        blocks, n_blocks = _get_blocks(inst.annotations, self.scope)
        for i_block in range(n_blocks):
            in_block = blocks == i_block
            present = set(descriptions[in_block])
            rule = next(
                (
                    x
                    for x in self.rules
                    if x.when is None or present.intersection(x.when)
                ),
                None,
            )
            if rule is None:
                msg = (
                    f"No rule to rename the events of block {i_block} "
                    f"(events: {sorted(present)})"
                )
                if self.on_unmatched == "raise":
                    raise_error(msg, klass=RuntimeError)
                elif self.on_unmatched == "warn":
                    logger.warning(msg)
                continue
            for old, new in rule.rename.items():
                descriptions[in_block & (descriptions == old)] = new
        _set_descriptions(
            inst, descriptions, np.ones(len(descriptions), dtype=bool)
        )
        return inst


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
