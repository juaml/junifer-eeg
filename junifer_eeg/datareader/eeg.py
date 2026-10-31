"""Provide the EEG DataReader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import zipfile
from pathlib import Path
from typing import ClassVar

import mne
import structlog
from junifer.api.decorators import register_datareader
from junifer.datareader import DefaultDataReader
from junifer.pipeline import WorkDirManager
from junifer.typing import Dependencies
from junifer.utils import raise_error


__all__ = ["EEGDataReader"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="datareader", step="datareader")

# Formats for the extensions that are not ambiguous
_extension_formats = {
    ".mff.zip": "egi",
    ".mff": "egi",
    ".fif": "fif",
    ".fif.gz": "fif",
    ".edf": "edf",
    ".bdf": "bdf",
    ".vhdr": "brainvision",
    ".set": "eeglab",
    ".cnt": "cnt",
}

# Reader functions for each format
_format_readers = {
    "egi": mne.io.read_raw_egi,
    "fif": mne.io.read_raw_fif,
    "edf": mne.io.read_raw_edf,
    "bdf": mne.io.read_raw_bdf,
    "brainvision": mne.io.read_raw_brainvision,
    "eeglab": mne.io.read_raw_eeglab,
    "cnt": mne.io.read_raw_cnt,
}


@register_datareader
class EEGDataReader(DefaultDataReader):
    """Concrete implementation for reading EEG data.

    The ``EEG`` data type is read with MNE as a :class:`mne.io.Raw`, with the
    data loaded in memory. The format is given by the ``format`` key of the
    data type (see :data:`_format_readers`), or by the file extension if it is
    not ambiguous. Zipped MFF directories (``.mff.zip``) are extracted to the
    element directory before reading. Other data types are read by
    :class:`junifer.datareader.DefaultDataReader`.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"mne", "junifer_eeg"}

    def _fit_transform(
        self,
        input: dict[str, dict],
        params: dict | None = None,
    ) -> dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        params : dict, optional
            Extra parameters for data types (default None).

        Returns
        -------
        dict
            The processed output as dictionary. The "data" key is added to
            each data type dictionary.

        """
        if params is None:
            params = {}
        # Read the other data types with the default DataReader
        others = {k: v for k, v in input.items() if k != "EEG"}
        out = super()._fit_transform(others, params) if others else {}
        if "EEG" in input:
            eeg = input["EEG"].copy()
            eeg["path"] = Path(eeg["path"])
            logger.info(f"Reading EEG from {eeg['path'].absolute()!s}")
            eeg["data"] = _read_eeg(
                path=eeg["path"],
                format=eeg.get("format"),
                read_params=params.get("EEG", {}),
            )
            self.update_meta(eeg, "datareader")
            out["EEG"] = eeg
        return out


def _get_format(path: Path, format: str | None) -> str:
    """Get the format of an EEG file.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file.
    format : str or None
        The format, if given by the DataGrabber.

    Returns
    -------
    str
        The format.

    Raises
    ------
    ValueError
        If the format is unknown or cannot be guessed from the extension.

    """
    if format is None:
        fname = path.name.lower()
        for ext, ext_format in _extension_formats.items():
            if fname.endswith(ext):
                format = ext_format
                break
        else:
            raise_error(
                f"Cannot guess the format of {path.name}, set the `format` "
                f"of the EEG data type to one of {list(_format_readers)}"
            )
    if format not in _format_readers:
        raise_error(
            f"Unknown EEG format {format}, valid formats are "
            f"{list(_format_readers)}"
        )
    return format


def _extract_mff_zip(path: Path) -> Path:
    """Extract a zipped MFF directory to the element directory.

    Parameters
    ----------
    path : pathlib.Path
        The path to the zip file.

    Returns
    -------
    pathlib.Path
        The path to the extracted MFF directory.

    Raises
    ------
    ValueError
        If the zip file does not contain exactly one directory.

    """
    tmpdir = WorkDirManager().get_element_tempdir(prefix="mffzip")
    logger.info(f"Extracting {path.name} to {tmpdir!s}")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(tmpdir)
    # Ignore the macOS metadata and hidden files
    contents = [
        x
        for x in tmpdir.iterdir()
        if x.name != "__MACOSX" and not x.name.startswith(".")
    ]
    if len(contents) != 1 or not contents[0].is_dir():
        raise_error(
            f"The zip file {path.name} must contain one MFF directory, "
            f"found: {[x.name for x in contents]}"
        )
    mff_dir = contents[0]
    # MNE needs the `.mff` extension
    if mff_dir.suffix != ".mff":
        mff_dir = mff_dir.rename(mff_dir.with_name(f"{mff_dir.name}.mff"))
    return mff_dir


def _read_eeg(
    path: Path, format: str | None, read_params: dict
) -> mne.io.BaseRaw:
    """Read an EEG file.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file.
    format : str or None
        The format, if given by the DataGrabber.
    read_params : dict
        Extra parameters for the MNE reader function.

    Returns
    -------
    mne.io.BaseRaw
        The data, loaded in memory.

    """
    format = _get_format(path, format)
    if path.name.lower().endswith(".zip"):
        path = _extract_mff_zip(path)
    reader = _format_readers[format]
    logger.info(f"EEG is of format {format}")
    return reader(path, preload=True, verbose="error", **read_params)
