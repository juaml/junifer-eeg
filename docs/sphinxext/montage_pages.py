"""Generate the pages of the built-in montages and their ROIs."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import matplotlib


matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import mne  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from ruamel.yaml import YAML  # noqa: E402


_ROIS_DIR = Path(__file__).parents[2] / "junifer_eeg" / "data" / "rois"
# Colors of junifer's logo: the channels out of and in the ROI
_CMAP = ListedColormap(["#d0d0d0", "#EF4567"])
_N_COLS = 4


def _read(fname: Path) -> tuple[dict, list[str]]:
    """Read a file of ROIs, and the notes of its header.

    The notes are the comment lines after the first empty comment line.

    """
    with fname.open() as f:
        content = YAML(typ="safe").load(f)
    header = []
    for line in fname.read_text().splitlines():
        if not line.startswith("#"):
            break
        header.append(line[1:].strip())
    notes = header[header.index("") + 1 :] if "" in header else []
    return content, notes


def _make_info(montages: list[str]) -> mne.Info:
    """Make the info with the positions of the montages.

    The positions are the ones of the first montage, with the channels of the
    other montages that are not in it.

    """
    ch_pos = {}
    for name in montages:
        montage = mne.channels.make_standard_montage(name)
        for ch, pos in montage.get_positions()["ch_pos"].items():
            ch_pos.setdefault(ch, pos)
    info = mne.create_info(list(ch_pos), 1.0, "eeg")
    info.set_montage(mne.channels.make_dig_montage(ch_pos, coord_frame="head"))
    return info


def _plot_rois(info: mne.Info, rois: dict, fname: Path) -> None:
    """Plot the channels of each ROI."""
    n_rows = -(-len(rois) // _N_COLS)
    fig, axes = plt.subplots(
        n_rows,
        _N_COLS,
        figsize=(3 * _N_COLS, 3 * n_rows),
        layout="constrained",
        squeeze=False,
    )
    for ax, (name, ch_names) in zip(axes.flat, rois.items()):
        idx = [info.ch_names.index(x) for x in ch_names]
        rest = [x for x in range(len(info.ch_names)) if x not in idx]
        mne.viz.plot_sensors(
            info,
            kind="topomap",
            ch_groups=[rest, idx],
            cmap=_CMAP,
            pointsize=8,
            linewidth=0,
            axes=ax,
            show=False,
        )
        ax.set_title(f"{name} ({len(ch_names)} channels)")
    for ax in axes.flat[len(rois) :]:
        ax.set_axis_off()
    fname.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fname, dpi=100)
    plt.close(fig)


def _literal(names: list[str]) -> str:
    """Format a list of names as inline literals."""
    return ", ".join(f"``{x}``" for x in names)


def generate(outdir: Path) -> None:
    """Generate the pages of the montages and the table of the montages.

    Parameters
    ----------
    outdir : pathlib.Path
        The directory of the pages (``docs/montages``).

    """
    outdir.mkdir(parents=True, exist_ok=True)
    table = [
        ".. list-table::",
        "   :header-rows: 1",
        "   :widths: 25 40 30 5",
        "",
        "   * - Montage",
        "     - System",
        "     - ROIs",
        "     - Plots",
    ]
    for fname in sorted(_ROIS_DIR.glob("*.yaml")):
        content, notes = _read(fname)
        system, montages, rois = (
            content["system"],
            content["montages"],
            content["rois"],
        )
        info = _make_info(list(montages))
        _plot_rois(info, rois, outdir / "images" / f"{fname.stem}.png")
        # The name of the system, and the details in parentheses
        title = system.partition(" (")[0]
        # Linked from the table, not in the navigation
        lines = [
            ":orphan:",
            "",
            f".. _montage_{fname.stem}:",
            "",
            title,
            "=" * len(title),
            "",
            f"System: {system}.",
            "",
            f"ROIs: {_literal(list(rois))}.",
            "",
            "Montages (the MNE montage with the positions):",
            "",
        ]
        lines += [f"* ``{name}``: {desc}" for name, desc in montages.items()]
        lines.append("")
        if notes:
            lines += [" ".join(notes), ""]
        lines += [
            "The channels of each ROI (highlighted), on the positions of "
            f"``{next(iter(montages))}``. The ``picks`` keep the channels of "
            "the ROI "
            "that are in the data.",
            "",
            f".. image:: images/{fname.stem}.png",
            f"   :alt: The ROIs of the {title}",
            "",
            "Channels",
            "--------",
            "",
        ]
        for name, ch_names in rois.items():
            lines += [
                f".. _montage_{fname.stem}_{name}:",
                "",
                f"``{name}``",
                "~" * (len(name) + 4),
                "",
                f"{_literal(ch_names)}.",
                "",
            ]
        (outdir / f"{fname.stem}.rst").write_text("\n".join(lines))
        # A row for each montage, with the ROIs of the system
        for name, desc in montages.items():
            table += [
                f"   * - ``{name}``",
                f"     - {desc[0].upper()}{desc[1:]}",
                f"     - {_literal(list(rois))}",
                f"     - :ref:`→ <montage_{fname.stem}>`",
            ]
    (outdir / "table.inc").write_text("\n".join(table) + "\n")


def _builder_inited(app) -> None:  # noqa: ANN001
    generate(Path(app.srcdir) / "montages")


def setup(app):  # noqa: ANN001, ANN201
    """Set up the extension."""
    app.connect("builder-inited", _builder_inited)
    return {"parallel_read_safe": True}
