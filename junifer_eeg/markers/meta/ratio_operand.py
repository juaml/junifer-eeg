"""Provide class for an operand of a ratio, a feature of a marker."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


__all__ = ["RatioOperand"]


class RatioOperand(BaseModel):
    """A feature of a marker, the numerator or the denominator of a ratio.

    Parameters
    ----------
    marker : str
        The base class of the marker (e.g., ``EEGPowerSpectralDensity``),
        whose values have the ``epochs`` and ``channels`` axes.
    feature : str
        The feature of the marker (e.g., ``theta``).
    params : dict, optional
        The parameters of the marker, without the aggregations (default
        empty).

    """

    model_config = ConfigDict(extra="forbid")

    marker: str
    feature: str
    params: dict[str, Any] = Field(default_factory=dict)
