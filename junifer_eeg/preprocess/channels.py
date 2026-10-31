"""Provide preprocessors for the channels of the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = [
    "EEGAverageReference",
    "EEGInterpolateBads",
    "EEGPickChannels",
    "EEGSetMontage",
]


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
