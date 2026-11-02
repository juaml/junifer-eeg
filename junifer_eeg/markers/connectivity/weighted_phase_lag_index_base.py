"""Provide base class for the weighted phase lag index (wPLI) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from typing import ClassVar

from .spectral_connectivity_base import EEGSpectralConnectivity


__all__ = ["EEGWeightedPhaseLagIndex"]


class EEGWeightedPhaseLagIndex(EEGSpectralConnectivity):
    """Base class for the weighted phase lag index (wPLI) markers.

    The wPLI is the consistency across epochs of the sign of the phase
    difference of each pair of channels, weighted by the magnitude of the
    imaginary part of the cross-spectrum, so it ignores the zero-lag
    interactions (e.g., volume conduction). See
    :class:`.EEGSpectralConnectivity`. Port of
    ``nice_sandbox.markers.WeightedPhaseLagIndex``.

    """

    _METHOD: ClassVar[str] = "wpli"
