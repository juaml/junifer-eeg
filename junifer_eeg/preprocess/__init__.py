"""Provide EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .base import EEGBasePreprocessor
from .channels import (
    EEGAverageReference,
    EEGInterpolateBads,
    EEGPickChannels,
    EEGRenameChannels,
    EEGSetMontage,
)
from .autorejection import EEGAutoReject
from .epochs import EEGEventEpochs, EEGFixedLengthEpochs
from .events import EEGDropEvents, EEGRenameEvents, RenameRule
from .filtering import EEGFilter, EEGNotchFilter, EEGResample
from .rejection import EEGAdaptiveRejection


__all__ = [
    "EEGAdaptiveRejection",
    "EEGAutoReject",
    "EEGAverageReference",
    "EEGBasePreprocessor",
    "EEGDropEvents",
    "EEGEventEpochs",
    "EEGFilter",
    "EEGFixedLengthEpochs",
    "EEGInterpolateBads",
    "EEGNotchFilter",
    "EEGPickChannels",
    "EEGRenameChannels",
    "EEGRenameEvents",
    "EEGResample",
    "EEGSetMontage",
    "RenameRule",
]
