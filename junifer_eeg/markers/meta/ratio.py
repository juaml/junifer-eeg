"""Provide class for a ratio between the features of two markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from nice-sandbox:
# Copyright (C) 2017 Federico Raimondo

from pydantic import BaseModel, ConfigDict

from .ratio_operand import RatioOperand


__all__ = ["Ratio"]


class Ratio(BaseModel):
    """A ratio between the features of two markers.

    Parameters
    ----------
    name : str
        The name of the ratio (the feature).
    numerator : RatioOperand
        The numerator.
    denominator : RatioOperand
        The denominator.

    """

    model_config = ConfigDict(extra="forbid")

    name: str
    numerator: RatioOperand
    denominator: RatioOperand
