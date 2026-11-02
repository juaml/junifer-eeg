"""Provide class for renaming the EEG channels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import re
from typing import Any

import mne
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error

from .base import EEGBasePreprocessor


__all__ = ["EEGRenameChannels"]


@register_preprocessor
class EEGRenameChannels(EEGBasePreprocessor):
    r"""Class for renaming the EEG channels.

    In order: the regular expression ``pattern`` is replaced by
    ``replacement`` in the names that match it (e.g., ``EEG FP1-REF`` to
    ``FP1``), the names in ``mapping`` are renamed, and, with
    ``montage_case``, the names are written as in the montage of the EEG
    data type, ignoring the case (e.g., ``FP1`` to ``Fp1``).

    Parameters
    ----------
    pattern : str or None, optional
        The regular expression to replace (see :func:`re.sub`). If None, no
        replacement (default None).
    replacement : str, optional
        The replacement of ``pattern``, with its groups as ``\1``
        (default ``"\1"``).
    mapping : dict of str and str or None, optional
        The new name of some channels (default None).
    montage_case : bool, optional
        Whether to use the case of the channel names of the montage
        (default False).

    """

    pattern: str | None = None
    replacement: str = r"\1"
    mapping: dict[str, str] | None = None
    montage_case: bool = False

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        names = {x: x for x in inst.ch_names}
        if self.pattern is not None:
            regex = re.compile(self.pattern)
            names = {
                x: regex.sub(self.replacement, y) if regex.search(y) else y
                for x, y in names.items()
            }
        if self.mapping is not None:
            names = {x: self.mapping.get(y, y) for x, y in names.items()}
        if self.montage_case:
            montage = mne.channels.make_standard_montage(input["montage"])
            by_lower = {x.lower(): x for x in montage.ch_names}
            names = {x: by_lower.get(y.lower(), y) for x, y in names.items()}
        new_names = list(names.values())
        repeated = sorted({x for x in new_names if new_names.count(x) > 1})
        if repeated:
            raise_error(f"Channels renamed to the same names: {repeated}")
        inst.rename_channels(
            {x: y for x, y in names.items() if x != y}, verbose="error"
        )
        return inst
