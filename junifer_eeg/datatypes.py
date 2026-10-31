"""Provide the EEG data type."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.datagrabber import DataType, DataTypeSchema, register_data_type


__all__ = ["EEG"]

# The montage of the recording, like `space` for MRI. The format is optional,
# needed when the file extension is ambiguous (e.g., `.raw`). If `files` is
# given, the pattern is a directory and all its files matching the `files`
# glob are concatenated (e.g., the blocks of a recording).
_eeg_schema: DataTypeSchema = {
    "mandatory": ["pattern", "montage"],
    "optional": {
        "format": {"mandatory": [], "optional": []},
        "files": {"mandatory": [], "optional": []},
    },
}

if "EEG" not in DataType.__members__:
    register_data_type(name="EEG", schema=_eeg_schema)

EEG = DataType("EEG")
