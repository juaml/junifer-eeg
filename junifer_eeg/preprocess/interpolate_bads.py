"""Provide class for interpolating the bad EEG channels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

from junifer.api.decorators import register_preprocessor

from .base import EEGBasePreprocessor


__all__ = ["EEGInterpolateBads"]


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
