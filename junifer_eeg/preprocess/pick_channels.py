"""Provide class for picking EEG channels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGPickChannels"]


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
