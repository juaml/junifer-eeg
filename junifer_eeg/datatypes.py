"""Provide the EEG data type."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import inspect
import os
import re
from pathlib import Path

from junifer.datagrabber import DataType, DataTypeSchema, register_data_type


__all__ = ["EEG", "get_eeg_companions"]

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

# The split FIF files: `<name>-<n>.fif` (MNE) or `..._split-<n>_...` (BIDS)
_BIDS_SPLIT = re.compile(r"_split-(\d+)_")


def _brainvision_companions(path: Path) -> list[Path]:
    """Get the data and marker files named in a BrainVision header."""
    out = []
    # The header is an INI file, `$b` is the name of the header without the
    # extension
    for line in path.read_text(encoding="latin-1").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in ("DataFile", "MarkerFile"):
            name = value.strip().replace("$b", path.stem)
            out.append(path.parent / name)
    return out


def _split_name(path: Path, i: int) -> Path:
    """Get the name of the split ``i`` of a FIF file."""
    match = _BIDS_SPLIT.search(path.name)
    if match is None:
        return path.with_name(f"{path.stem}-{i}{path.suffix}")
    width = len(match.group(1))
    return path.with_name(_BIDS_SPLIT.sub(f"_split-{i:0{width}d}_", path.name))


def _fif_companions(path: Path) -> list[Path]:
    """Get the next split files of a FIF file."""
    match = _BIDS_SPLIT.search(path.name)
    i = 1 if match is None else int(match.group(1)) + 1
    out = []
    # The links of the files are in the dataset, even if not got
    while os.path.lexists(_split_name(path, i)):
        out.append(_split_name(path, i))
        i += 1
    return out


def get_eeg_companions(path: Path) -> list[Path]:
    """Get the other files needed to read an EEG recording.

    The files that MNE reads with the recording: the data and marker files
    of a BrainVision header (``.vhdr``), the data file of an EEGLAB dataset
    (``.fdt``, if not in the ``.set``) and the next files of a split FIF
    file. The recordings in a directory (e.g., EGI ``.mff``) have no
    companions, as the directory is got.

    The DataLad DataGrabbers call it once the recording is got, which also
    installs its sub-dataset (e.g., one sub-dataset per subject), and then
    get the companions. So the recording can be read (e.g., the BrainVision
    header) and the links of the other files of its sub-dataset are there,
    but not their content: the files are found with ``os.path.lexists``,
    not ``exists``.

    Parameters
    ----------
    path : pathlib.Path
        The path of the recording, got (with its content).

    Returns
    -------
    list of pathlib.Path
        The other files.

    """
    if path.is_dir():
        return []
    suffix = path.suffix.lower()
    if suffix == ".vhdr":
        return _brainvision_companions(path)
    if suffix == ".set":
        fdt = path.with_suffix(".fdt")
        return [fdt] if os.path.lexists(fdt) else []
    if suffix == ".fif":
        return _fif_companions(path)
    return []


if "EEG" not in DataType.__members__:
    # The companions are only supported by the junifer versions with
    # juaml/junifer#539: remove the check once junifer-eeg requires one
    if "companions" in inspect.signature(register_data_type).parameters:
        register_data_type(
            name="EEG", schema=_eeg_schema, companions=get_eeg_companions
        )
    else:
        register_data_type(name="EEG", schema=_eeg_schema)

EEG = DataType("EEG")
