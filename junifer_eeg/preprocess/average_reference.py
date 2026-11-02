"""Provide class for re-referencing EEG data to the average."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGAverageReference"]


@register_preprocessor
class EEGAverageReference(EEGBasePreprocessor):
    """Class for re-referencing EEG data to the average.

    The average reference is added as a projector and applied. The bad
    channels are excluded from the average.

    """

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        inst.set_eeg_reference("average", projection=True, verbose="error")
        return inst.apply_proj(verbose="error")
