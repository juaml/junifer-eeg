"""Provide EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from .base import EEGBasePreprocessor
from .average_reference import EEGAverageReference
from .interpolate_bads import EEGInterpolateBads
from .pick_channels import EEGPickChannels
from .rename_channels import EEGRenameChannels
from .set_montage import EEGSetMontage
from .auto_reject import EEGAutoReject
from .event_epochs import EEGEventEpochs
from .fixed_length_epochs import EEGFixedLengthEpochs
from .drop_events import EEGDropEvents
from .rename_events import EEGRenameEvents
from .rename_rule import RenameRule
from .filter import EEGFilter
from .notch_filter import EEGNotchFilter
from .resample import EEGResample
from .adaptive_rejection import EEGAdaptiveRejection


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
