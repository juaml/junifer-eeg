"""Provide class for a contrast of the epochs of two sets of conditions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from pydantic import BaseModel, ConfigDict


__all__ = ["Contrast"]


class Contrast(BaseModel):
    """A contrast between the epochs of two sets of conditions.

    Parameters
    ----------
    name : str
        The name of the contrast (the feature).
    condition_a : list of str
        The conditions (event names) of the epochs of the first set.
    condition_b : list of str
        The conditions (event names) of the epochs of the second set.
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).
    picks : str or list of str or None, optional
        The channels reduced by the ``channels`` aggregation step, as names
        of ROIs or channels (see :class:`.AggregationStep`). If None, the
        picks of the step (default None).

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    condition_a: list[str]
    condition_b: list[str]
    tmin: float | None = None
    tmax: float | None = None
    picks: str | list[str] | None = None
