"""Provide base class for the phase locking value (PLV) markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from typing import ClassVar

from .spectral_connectivity_base import EEGSpectralConnectivity


__all__ = ["EEGPhaseLockingValue"]


class EEGPhaseLockingValue(EEGSpectralConnectivity):
    """Base class for the phase locking value (PLV) markers.

    The PLV is the consistency across epochs of the phase difference of each
    pair of channels. See :class:`.EEGSpectralConnectivity`. Port of
    ``nice_sandbox.markers.PhaseLockingValue``.

    """

    _METHOD: ClassVar[str] = "plv"
