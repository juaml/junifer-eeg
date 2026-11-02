"""Provide the base class for EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Sequence
from typing import Any, ClassVar

import mne
from junifer.datagrabber import DataType
from junifer.preprocess import BasePreprocessor
from junifer.typing import Dependencies
from junifer.utils import raise_error

from ..datatypes import EEG


__all__ = ["EEGBasePreprocessor"]


class EEGBasePreprocessor(BasePreprocessor):
    """Base class for EEG preprocessors.

    The data of the ``EEG`` data type is an MNE object, changed in place.
    Each preprocessor works on continuous data (:class:`mne.io.BaseRaw`),
    epoched data (:class:`mne.BaseEpochs`) or both, as set by
    ``_VALID_INSTANCES``.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"mne", "junifer_eeg"}
    _VALID_DATA_TYPES: ClassVar[Sequence[DataType]] = [EEG]
    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (
        mne.io.BaseRaw,
        mne.BaseEpochs,
    )

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object (default None).

        Returns
        -------
        dict
            The input with the preprocessed data.

        Raises
        ------
        TypeError
            If the data is not of a valid MNE type for the preprocessor.

        """
        inst = input["data"]
        if not isinstance(inst, self._VALID_INSTANCES):
            valid = " or ".join(x.__name__ for x in self._VALID_INSTANCES)
            raise_error(
                f"{self.__class__.__name__} needs {valid} data, got "
                f"{type(inst).__name__}. Check the order of the "
                "preprocessors.",
                klass=TypeError,
            )
        input["data"] = self._preprocess(inst, input)
        return input

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        """Preprocess the MNE object.

        Parameters
        ----------
        inst : mne.io.BaseRaw or mne.BaseEpochs
            The data.
        input : dict
            The Junifer Data object item, e.g., to get the ``montage``.

        Returns
        -------
        mne.io.BaseRaw or mne.BaseEpochs
            The preprocessed data.

        """
        raise_error(
            msg="Concrete classes need to implement _preprocess().",
            klass=NotImplementedError,
        )
