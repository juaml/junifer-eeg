"""Provide the preprocessor for rejecting bad epochs with autoreject."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-extensions:
# Copyright (C) 2017-2018 Federico Raimondo

from typing import Any, ClassVar, Literal

import mne
import numpy as np
import structlog
from autoreject import AutoReject
from junifer.api.decorators import register_preprocessor
from junifer.typing import Dependencies

from .base import EEGBasePreprocessor
from .rejection import check_min_epochs


__all__ = ["EEGAutoReject"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="preprocess", step="preprocessing")


@register_preprocessor
class EEGAutoReject(EEGBasePreprocessor):
    """Class for repairing and rejecting bad epochs with autoreject.

    The local autoreject (Jas et al. 2017) learns a peak-to-peak threshold
    for each channel with cross-validation. In each epoch, the channels
    exceeding their threshold are interpolated if they are at most
    ``n_interpolate``, and the epoch is dropped if they are more than
    ``consensus`` of the channels (both chosen by cross-validation among the
    candidates). Only the good EEG channels are used. Port of the
    ``autoreject`` option of the ``icm/lg/raw/egi`` preprocessing of NICE.

    Needs the channel positions (see :class:`.EEGSetMontage`).

    Parameters
    ----------
    n_interpolate : list of int or None, optional
        The candidates for the maximum number of channels to interpolate in
        an epoch. If None, autoreject's default (default None).
    consensus : list of float or None, optional
        The candidates for the proportion of bad channels to drop an epoch.
        If None, autoreject's default (default None).
    cv : int, optional
        The number of folds of the cross-validation (default 10).
    thresh_method : {"bayesian_optimization", "random_search"}, optional
        The method to find the thresholds (default "bayesian_optimization").
    seed : int or None, optional
        The seed of the cross-validation and the threshold search
        (default None).
    n_jobs : int, optional
        The number of parallel jobs (default 1).
    min_epochs : float or int or None, optional
        The minimum number (int) or proportion (float) of epochs remaining,
        out of the epochs before rejection. If None, it is not checked
        (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {
        "mne",
        "autoreject",
        "junifer_eeg",
    }
    _VALID_INSTANCES: ClassVar[tuple[type, ...]] = (mne.BaseEpochs,)

    n_interpolate: list[int] | None = None
    consensus: list[float] | None = None
    cv: int = 10
    thresh_method: Literal["bayesian_optimization", "random_search"] = (
        "bayesian_optimization"
    )
    seed: int | None = None
    n_jobs: int = 1
    min_epochs: float | int | None = None

    def _preprocess(self, inst: Any, input: dict[str, Any]) -> Any:
        picks = mne.pick_types(inst.info, eeg=True, exclude="bads")
        n_epochs = len(inst)
        ar = AutoReject(
            n_interpolate=(
                None
                if self.n_interpolate is None
                else np.array(self.n_interpolate)
            ),
            consensus=(
                None if self.consensus is None else np.array(self.consensus)
            ),
            cv=self.cv,
            picks=picks,
            thresh_method=self.thresh_method,
            random_state=self.seed,
            n_jobs=self.n_jobs,
            verbose=False,
        )
        inst, reject_log = ar.fit_transform(inst, return_log=True)
        n_interpolated = int((reject_log.labels == 2).sum())
        logger.info(
            f"autoreject: {int(reject_log.bad_epochs.sum())} bad epochs, "
            f"{n_interpolated} channels interpolated in the epochs "
            f"(n_interpolate {ar.n_interpolate_['eeg']}, consensus "
            f"{ar.consensus_['eeg']})"
        )
        check_min_epochs(inst, n_epochs, self.min_epochs)
        return inst
