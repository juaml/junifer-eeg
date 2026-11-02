"""Provide the aggregation of the axes of the EEG markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from collections.abc import Callable
from typing import Any, Literal

import numpy as np
from junifer.stats import AggFunc, get_aggfunc_by_name
from junifer.utils import raise_error
from pydantic import BaseModel, ConfigDict


__all__ = ["AggregationStep", "Axis", "get_aggregation_function"]


Axis = Literal["epochs", "channels", "channels_y", "times", "folds"]


class AggregationStep(BaseModel):
    """An aggregation step, reducing one axis of a marker.

    Parameters
    ----------
    axis : {"epochs", "channels", "channels_y", "times", "folds"}
        The axis to reduce.
    method : str
        The aggregation function. See :func:`get_aggregation_function`.
    method_params : dict or None, optional
        The parameters of the aggregation function (default None).
    picks : str or list of str or None, optional
        The channels to aggregate (only for ``channels`` and ``channels_y``),
        as names of ROIs for the montage of the data (their channels in the
        data) or of channels, concatenated (e.g., ``[fz, cz]``). If None, all
        the channels are aggregated (default None).

    """

    model_config = ConfigDict(extra="forbid")

    axis: Axis
    method: str
    method_params: dict[str, Any] | None = None
    picks: str | list[str] | None = None


def _sum(a: np.ndarray, axis: int = 0) -> np.ndarray:
    """Sum the values."""
    return np.sum(a, axis=axis)


def _median(a: np.ndarray, axis: int = 0) -> np.ndarray:
    """Compute the median of the values."""
    return np.median(a, axis=axis)


def entropy(a: np.ndarray, axis: int = 0) -> np.ndarray:
    """Compute the normalized entropy of a distribution (as in NICE).

    Parameters
    ----------
    a : numpy.ndarray
        The probabilities.
    axis : int, optional
        The axis of the distribution (default 0).

    Returns
    -------
    numpy.ndarray
        The entropy, divided by the maximum entropy.

    """
    with np.errstate(divide="ignore", invalid="ignore"):
        return -np.nansum(a * np.log(a), axis=axis) / np.log(a.shape[axis])


# Aggregation functions besides the ones of junifer
_functions = {
    "sum": _sum,
    "median": _median,
    "entropy": entropy,
}


def get_aggregation_function(
    name: str, params: dict[str, Any] | None = None
) -> Callable:
    """Get an aggregation function by its name.

    Parameters
    ----------
    name : str
        The name of the function: ``sum``, ``median``, ``entropy`` or one of
        :enum:`junifer.stats.AggFunc` (e.g., ``mean``, ``std`` or
        ``trim_mean``).
    params : dict or None, optional
        The parameters of the function (default None).

    Returns
    -------
    callable
        The function, called as ``func(data, axis=axis)``.

    Raises
    ------
    ValueError
        If the function is unknown.

    """
    if name in _functions:
        if params:
            raise_error(f"Aggregation function {name} takes no parameters")
        return _functions[name]
    if name not in AggFunc.__members__.values():
        raise_error(
            f"Unknown aggregation function {name}, options are "
            f"{sorted([*_functions, *AggFunc])}"
        )
    return get_aggfunc_by_name(name, params)
