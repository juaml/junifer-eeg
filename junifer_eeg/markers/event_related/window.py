"""Provide class for a time window of the epochs of some conditions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from pydantic import BaseModel, ConfigDict


__all__ = ["Window"]


class Window(BaseModel):
    """A time window of the epochs of some conditions.

    Parameters
    ----------
    name : str
        The name of the window (the feature).
    tmin : float or None, optional
        The start of the window. If None, from the start (default None).
    tmax : float or None, optional
        The end of the window. If None, until the end (default None).
    conditions : list of str or None, optional
        The conditions (event names) of the epochs to use. If None, all the
        epochs are used (default None).
    picks : str or list of str or None, optional
        The channels reduced by the ``channels`` aggregation step, as names
        of ROIs or channels (see :class:`.AggregationStep`). If None, the
        picks of the step (default None).

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    tmin: float | None = None
    tmax: float | None = None
    conditions: list[str] | None = None
    picks: str | list[str] | None = None
