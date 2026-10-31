"""Provide the EEG decoding markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .window_decoding import Decoder, EEGWindowDecoding, EEGWindowDecodingScalar


__all__ = ["Decoder", "EEGWindowDecoding", "EEGWindowDecodingScalar"]
