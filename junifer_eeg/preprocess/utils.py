"""Provide utilities for the EEG preprocessors."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-extensions:
# Copyright (C) 2017-2018 Federico Raimondo

import mne
from junifer.utils import raise_error


__all__ = ["check_min_epochs"]


def check_min_epochs(
    inst: mne.BaseEpochs, n_epochs: int, min_epochs: float | int | None
) -> None:
    """Check the number of epochs remaining after a rejection.

    Parameters
    ----------
    inst : mne.BaseEpochs
        The epochs remaining.
    n_epochs : int
        The number of epochs before the rejection.
    min_epochs : float or int or None
        The minimum number (int) or proportion (float) of epochs remaining.
        If None, it is not checked.

    Raises
    ------
    RuntimeError
        If fewer than ``min_epochs`` epochs remain.

    """
    if min_epochs is None:
        return
    if isinstance(min_epochs, float):
        min_epochs = int(n_epochs * min_epochs)
    if len(inst) < min_epochs:
        raise_error(
            f"Cannot clean data: only {len(inst)} out of {n_epochs} "
            f"epochs remain (minimum {min_epochs}).",
            klass=RuntimeError,
        )
