"""Provide the EEG decoding markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .decoder import Decoder
from .window_decoding_base import EEGWindowDecoding
from .window_decoding_scalar import EEGWindowDecodingScalar


__all__ = ["Decoder", "EEGWindowDecoding", "EEGWindowDecodingScalar"]
