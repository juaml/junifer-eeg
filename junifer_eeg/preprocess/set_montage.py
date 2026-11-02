"""Provide class for setting the montage of the EEG data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import mne
from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGSetMontage"]


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
