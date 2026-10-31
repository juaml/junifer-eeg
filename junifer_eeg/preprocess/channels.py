"""Provide preprocessors for the channels of the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import re
from typing import Any

import mne
from junifer.api.decorators import register_preprocessor
from junifer.utils import raise_error

from .base import EEGBasePreprocessor


__all__ = [
    "EEGAverageReference",
    "EEGInterpolateBads",
    "EEGPickChannels",
    "EEGRenameChannels",
    "EEGSetMontage",
]


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


@register_preprocessor
class EEGPickChannels(EEGBasePreprocessor):
    """Class for picking EEG channels.

    Parameters
    ----------
    picks : str or list of str
        The channels to keep, as channel types (e.g., ``eeg``) or names. See
        :meth:`mne.io.Raw.pick` (default "eeg").
    exclude : list of str, optional
        The channels to remove from ``picks``. The channels that are not in
        the data are ignored (default None).

    """

    picks: str | list[str] = "eeg"
    exclude: list[str] | None = None

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        exclude = [x for x in (self.exclude or []) if x in inst.ch_names]
        return inst.pick(self.picks, exclude=exclude)


@register_preprocessor
class EEGSetMontage(EEGBasePreprocessor):
    """Class for setting the standard montage of the EEG data.

    The montage is the ``montage`` of the EEG data type (given by the
    DataGrabber), replacing the channel positions of the file, so all the
    files of a montage have the same positions.

    Parameters
    ----------
    on_missing : {"raise", "warn", "ignore"}, optional
        What to do with the channels that are not in the montage
        (default "raise").

    """

    on_missing: str = "raise"

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        montage = mne.channels.make_standard_montage(input["montage"])
        return inst.set_montage(
            montage, on_missing=self.on_missing, verbose="error"
        )


@register_preprocessor
class EEGAverageReference(EEGBasePreprocessor):
    """Class for re-referencing EEG data to the average.

    The average reference is added as a projector and applied. The bad
    channels are excluded from the average.

    """

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        inst.set_eeg_reference("average", projection=True, verbose="error")
        return inst.apply_proj(verbose="error")


@register_preprocessor
class EEGInterpolateBads(EEGBasePreprocessor):
    """Class for interpolating the bad EEG channels.

    Parameters
    ----------
    reset_bads : bool, optional
        Whether to clear the bad channels after interpolating them
        (default True).
    method : dict or None, optional
        The interpolation method for each channel type. See
        :meth:`mne.io.Raw.interpolate_bads` (default None).

    """

    reset_bads: bool = True
    method: dict[str, str] | None = None

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        return inst.interpolate_bads(
            reset_bads=self.reset_bads, method=self.method, verbose="error"
        )
