"""Provide EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .base import EEGBasePreprocessor
from .channels import (
    EEGAverageReference,
    EEGInterpolateBads,
    EEGPickChannels,
    EEGSetMontage,
)
from .epochs import EEGFixedLengthEpochs
from .filtering import EEGFilter, EEGNotchFilter, EEGResample
from .rejection import EEGAdaptiveRejection


__all__ = [
    "EEGAdaptiveRejection",
    "EEGAverageReference",
    "EEGBasePreprocessor",
    "EEGFilter",
    "EEGFixedLengthEpochs",
    "EEGInterpolateBads",
    "EEGNotchFilter",
    "EEGPickChannels",
    "EEGResample",
    "EEGSetMontage",
]
