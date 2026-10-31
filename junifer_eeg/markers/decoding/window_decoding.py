"""Provide the window decoding markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Any, ClassVar

import mne
import numpy as np
from junifer.api.decorators import register_marker
from junifer.typing import Dependencies
from junifer.utils import raise_error
from pydantic import BaseModel, ConfigDict
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_selection import SelectPercentile, f_classif
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from ..aggregation import Axis
from ..base import EEGBaseMarker, ScalarMixin
from ..utils import get_epochs, get_picks, time_mask


__all__ = [
    "Decoder",
    "EEGWindowDecoding",
    "EEGWindowDecodingScalar",
]


class Decoder(BaseModel):
    """A classification of the epochs of two sets of conditions.

    Parameters
    ----------
    name : str
        The name of the decoder (the feature).
    condition_a : list of str
        The conditions (event names) of the epochs of the positive class.
    condition_b : list of str
        The conditions (event names) of the epochs of the negative class.
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    condition_a: list[str]
    condition_b: list[str]
    tmin: float | None = None
    tmax: float | None = None


class EEGWindowDecoding(EEGBaseMarker):
    """Base class for the window decoding markers.

    For each decoder (a feature), the epochs of ``condition_a`` and
    ``condition_b`` are classified from all the channels and samples of the
    window, with a stratified K-fold cross-validation (shuffled). The
    classifier standardizes the features, selects the ``percentile`` best
    ones (ANOVA F-value) and fits a linear SVM. The samples are weighted by
    the inverse of the number of epochs of their condition. The value of
    each fold is the ROC AUC of the predicted probabilities of the test
    epochs. The probabilities are calibrated with Platt scaling (a sigmoid
    fitted with an internal 5-fold cross-validation of the training epochs).
    Port of ``nice.markers.WindowDecoding``, which computed the AUC of the
    predicted classes instead.

    Parameters
    ----------
    decoders : list of Decoder
        The decoders.
    percentile : float, optional
        The percentile of the features to select (default 10).
    C : float, optional
        The regularization parameter of the SVM (default 1.0).
    n_splits : int, optional
        The number of folds. It is reduced to half the number of epochs if
        there are fewer (default 10).
    seed : int, optional
        The seed of the shuffling of the folds (default 0).
    aggregations : dict of str and list of AggregationStep
        The aggregations to compute. See :class:`.EEGBaseMarker`.
    on : ``DataType.EEG`` or None, optional
        The data type to compute the marker on (default None).
    name : str or None, optional
        The name of the marker (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {
        "mne",
        "numpy",
        "scikit-learn",
        "junifer_eeg",
    }
    _AXES: ClassVar[tuple[Axis, ...]] = ("folds",)

    decoders: list[Decoder]
    percentile: float = 10
    C: float = 1.0
    n_splits: int = 10
    seed: int = 0

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        super().validate_marker_params()
        if len(self.decoders) == 0:
            raise_error("At least one decoder is needed")
        names = [x.name for x in self.decoders]
        if len(set(names)) != len(names):
            raise_error(f"The names of the decoders must be unique: {names}")
        if self.n_splits < 2:
            raise_error("`n_splits` must be at least 2")

    def compute_values(
        self, input: dict[str, Any]
    ) -> tuple[list[np.ndarray], list[str], list[str]]:
        """Compute the AUC of each fold, for each decoder.

        Parameters
        ----------
        input : dict
            The ``EEG`` item of the data object, with the epochs as ``data``.

        Returns
        -------
        list of numpy.ndarray
            The values of each decoder, shape (n_folds, 1).
        list of str
            The names of the features.
        list of str
            The names of the channels.

        """
        epochs = get_epochs(input)
        picks = get_picks(epochs.info)
        values = [self._decode(epochs, picks, x) for x in self.decoders]
        ch_names = [epochs.ch_names[x] for x in picks]
        return values, [x.name for x in self.decoders], ch_names

    def _decode(
        self, epochs: mne.BaseEpochs, picks: np.ndarray, decoder: Decoder
    ) -> np.ndarray:
        """Decode the conditions of a decoder.

        Parameters
        ----------
        epochs : mne.BaseEpochs
            The epochs.
        picks : numpy.ndarray
            The indices of the channels.
        decoder : Decoder
            The decoder.

        Returns
        -------
        numpy.ndarray
            The AUC of each fold, shape (n_folds, 1).

        """
        mask = time_mask(
            epochs.times, decoder.tmin, decoder.tmax, epochs.info["sfreq"]
        )
        codes = epochs.events[:, 2]
        # Class b (0) first, then class a (1), as in NICE
        selections = []
        for conditions in (decoder.condition_b, decoder.condition_a):
            ids = [
                epochs.event_id[x] for x in conditions if x in epochs.event_id
            ]
            selection = np.flatnonzero(np.isin(codes, ids))
            if len(selection) == 0:
                raise_error(
                    f"Decoder {decoder.name}: no epochs of the conditions "
                    f"{conditions}"
                )
            selections.append(selection)
        selection = np.concatenate(selections)
        y = np.r_[np.zeros(len(selections[0])), np.ones(len(selections[1]))]
        X = epochs.get_data(picks=picks)[selection][..., mask]  # noqa: N806
        X = X.reshape(len(X), -1)  # noqa: N806
        # The weight of each epoch is the inverse of the epochs of its event
        this_codes = codes[selection]
        _, inverse, counts = np.unique(
            this_codes, return_inverse=True, return_counts=True
        )
        sample_weight = 1.0 / counts[inverse]

        n_splits = int(min(self.n_splits, len(y) / 2))
        cv = StratifiedKFold(
            n_splits=n_splits, shuffle=True, random_state=self.seed
        )
        clf = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "anova",
                    SelectPercentile(f_classif, percentile=self.percentile),
                ),
                (
                    "svc",
                    CalibratedClassifierCV(
                        SVC(C=self.C, kernel="linear"),
                        method="sigmoid",
                        ensemble=False,
                    ),
                ),
            ]
        )
        scores = []
        for train, test in cv.split(X, y):
            clf.fit(
                X[train], y[train], svc__sample_weight=sample_weight[train]
            )
            probas = clf.predict_proba(X[test])[:, 1]
            scores.append(
                roc_auc_score(
                    y[test], probas, sample_weight=sample_weight[test]
                )
            )
        return np.array(scores)[:, np.newaxis]


@register_marker
class EEGWindowDecodingScalar(ScalarMixin, EEGWindowDecoding):
    """Class for the window decoding markers, reduced to scalars.

    See :class:`.EEGWindowDecoding` and :class:`.ScalarMixin`.

    """
