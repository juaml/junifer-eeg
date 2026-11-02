"""Provide class for the parameters of the (w)SMI estimation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

from typing import Literal

from pydantic import BaseModel, ConfigDict


__all__ = ["SMIEstimatorParams"]


class SMIEstimatorParams(BaseModel):
    """Parameters of the (w)SMI estimation.

    See :class:`.EEGSymbolicMutualInformation` for the parameters.

    """

    model_config = ConfigDict(extra="forbid")

    tmin: float | None = None
    tmax: float | None = None
    kernel: int = 3
    tau: int = 8
    method: Literal["weighted", "smi"] = "weighted"
    csd: bool = True
    filter_freq: float | None = None
