"""Provide the testing DataGrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import ClassVar

from junifer.datagrabber import BaseDataGrabber, DataType
from junifer.utils import raise_error

from ..datasets import fetch_tueg
from ..datatypes import EEG


__all__ = ["TUEGTestingDataGrabber"]


class TUEGTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for recordings of the TUH EEG Corpus (TUEG).

    The first recording of each subject, downloaded with
    :func:`.fetch_tueg`: clinical EDF files with the channels of the 10-20
    system, named as ``EEG FP1-REF`` (or ``EEG FP1-LE``, for the
    linked-ears reference), and non-EEG channels (e.g., the ECG). The
    montage is ``colin27_1020``, for the 10-20 names (e.g., ``Fp1``).

    The TUEG is distributed by the Neural Engineering Data Consortium (NEDC)
    of Temple University, under a data agreement: register at
    https://isip.piconepress.com/projects/nedc/html/tuh_eeg/ before using it.

    Parameters
    ----------
    subjects : list of str, optional
        The subjects (default the first recordings of ``aaaaaaab``,
        ``aaaaaaaf``, ``aaaaaaag`` and ``aaaaaaai``, from 2 to 6 minutes).
    datadir : pathlib.Path, optional
        The directory to download the corpus to (default
        ``~/junifer_eeg_data/tueg``).

    """

    types: list[DataType] = [EEG]  # noqa: RUF012
    datadir: Path = Path.home() / "junifer_eeg_data" / "tueg"
    subjects: list[str] = [  # noqa: RUF012
        "aaaaaaab",
        "aaaaaaaf",
        "aaaaaaag",
        "aaaaaaai",
    ]

    _MONTAGE: ClassVar[str] = "colin27_1020"
    _GROUP: ClassVar[str] = "000"
    _edfdir: Path | None = None

    def __enter__(self) -> "TUEGTestingDataGrabber":
        """Implement context entry, downloading the recordings.

        Returns
        -------
        TUEGTestingDataGrabber

        """
        self._edfdir = fetch_tueg(
            self.subjects, path=self.datadir, group=self._GROUP
        )
        return self

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        Returns
        -------
        list of str
            The element keys.

        """
        return ["subject"]

    def get_elements(self) -> list[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return list(self.subjects)

    def get_item(self, subject: str) -> dict[str, dict]:
        """Implement indexing support.

        Parameters
        ----------
        subject : str
            The subject to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        Raises
        ------
        RuntimeError
            If the DataGrabber is not used as a context manager.

        """
        if self._edfdir is None:
            raise_error(
                "TUEGTestingDataGrabber must be used as a context manager "
                "(`with`), which downloads the recordings",
                klass=RuntimeError,
            )
        # The first session, montage and recording
        path = sorted(
            (self._edfdir / self._GROUP / subject).glob("*/*/*.edf")
        )[0]
        return {"EEG": {"path": path, "montage": self._MONTAGE}}
