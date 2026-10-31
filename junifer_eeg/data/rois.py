"""Provide the registry of EEG regions of interest (ROIs)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Any

from junifer.api.decorators import register_data_registry
from junifer.data import BasePipelineDataRegistry, get_data
from junifer.utils import raise_error
from ruamel.yaml import YAML


__all__ = ["EEGROIRegistry", "get_roi_channels"]


_ROIS_DIR = Path(__file__).parent / "rois"


@register_data_registry("eeg_roi")
class EEGROIRegistry(BasePipelineDataRegistry):
    """Class for the registry of EEG ROIs.

    An ROI is a list of channel names, defined for a montage. The built-in
    ROIs are read from the ``data/rois/<montage>.yaml`` files.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__()
        yaml = YAML(typ="safe")
        for fname in sorted(_ROIS_DIR.glob("*.yaml")):
            with fname.open() as f:
                rois = yaml.load(f)
            for name, ch_names in rois.items():
                self._registry[f"{fname.stem}/{name}"] = list(ch_names)

    def register(
        self,
        montage: str,
        name: str,
        ch_names: list[str],
        overwrite: bool = False,
    ) -> None:
        """Register an ROI.

        Parameters
        ----------
        montage : str
            The montage the ROI is defined for.
        name : str
            The name of the ROI.
        ch_names : list of str
            The channel names of the ROI.
        overwrite : bool, optional
            Whether to overwrite an existing ROI (default False).

        Raises
        ------
        ValueError
            If the ROI is already registered and ``overwrite=False``.

        """
        key = f"{montage}/{name}"
        if key in self._registry and not overwrite:
            raise_error(
                f"ROI {name} already registered for {montage}. "
                "Set `overwrite=True` to update it."
            )
        self._registry[key] = list(ch_names)

    def deregister(self, montage: str, name: str) -> None:
        """De-register an ROI.

        Parameters
        ----------
        montage : str
            The montage the ROI is defined for.
        name : str
            The name of the ROI.

        """
        _ = self._registry.pop(f"{montage}/{name}")

    def load(self, montage: str, name: str) -> list[str]:
        """Load an ROI.

        Parameters
        ----------
        montage : str
            The montage the ROI is defined for.
        name : str
            The name of the ROI.

        Returns
        -------
        list of str
            The channel names of the ROI.

        Raises
        ------
        ValueError
            If the ROI is not defined for the montage.

        """
        key = f"{montage}/{name}"
        if key not in self._registry:
            available = [
                k.split("/", 1)[1]
                for k in self._registry
                if k.startswith(f"{montage}/")
            ]
            raise_error(
                f"ROI {name} not defined for montage {montage}. "
                f"Available ROIs: {available}"
            )
        return list(self._registry[key])

    def get(
        self,
        rois: str,
        target_data: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> list[str]:
        """Get the channels of an ROI, for the montage of the target data.

        Parameters
        ----------
        rois : str
            The name of the ROI.
        target_data : dict
            The corresponding item of the data object, with the ``montage``.
        extra_input : dict, optional
            The other fields in the data object (default None).

        Returns
        -------
        list of str
            The channel names of the ROI.

        """
        return self.load(montage=target_data["montage"], name=rois)


def get_roi_channels(
    picks: str | list[str],
    target_data: dict[str, Any],
) -> list[str]:
    """Get the channel names of a channel selection.

    Parameters
    ----------
    picks : str or list of str
        The name of an ROI for the montage of ``target_data``, or the list of
        channel names.
    target_data : dict
        The corresponding item of the data object, with the ``montage``.

    Returns
    -------
    list of str
        The channel names.

    """
    if isinstance(picks, str):
        return get_data(kind="eeg_roi", names=picks, target_data=target_data)
    return list(picks)
