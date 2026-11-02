"""Provide class for renaming the events of continuous EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Literal

import mne
import numpy as np
import structlog
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error

from ._events import _get_blocks, _set_descriptions
from .base import EEGBasePreprocessor
from .rename_rule import RenameRule


__all__ = ["EEGRenameEvents"]


_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="preprocess", step="preprocess")


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
