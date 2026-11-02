"""Provide class for a rule for renaming the events (annotations)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pydantic import BaseModel, ConfigDict


__all__ = ["RenameRule"]


class RenameRule(BaseModel):
    """A rule for renaming the events (annotations).

    Parameters
    ----------
    when : list of str or None, optional
        The rule applies if any of these events is present. If None, the rule
        always applies (default None).
    rename : dict of str and str
        The new name of each event. The other events are kept.

    """

    model_config = ConfigDict(extra="forbid")

    when: list[str] | None = None
    rename: dict[str, str]
