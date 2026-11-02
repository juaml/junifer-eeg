"""Provide tests for the datasets."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import io
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from junifer_eeg.datasets import fetch_tueg


_URL = "https://isip.piconepress.com/projects/nedc/data/tuh_eeg/tuh_eeg"
_BASE = f"{_URL}/v2.0.2/edf/000"


def _index(*names: str) -> bytes:
    """Make an Apache directory index."""
    links = [
        '<a href="?C=N;O=D">Name</a>',
        '<a href="/projects/nedc/data/tuh_eeg/">Parent Directory</a>',
        *[f'<a href="{x}">{x}</a>' for x in names],
        '<a href="mailto:x@y.com">x</a>',
    ]
    return "\n".join(links).encode()


_SERVER = {
    f"{_BASE}/aaaaaaaf/": _index("s002_2003/", "s001_2002/"),
    f"{_BASE}/aaaaaaaf/s001_2002/": _index("02_tcp_le/"),
    f"{_BASE}/aaaaaaaf/s001_2002/02_tcp_le/": _index(
        "aaaaaaaf_s001_t001.edf", "aaaaaaaf_s001_t000.edf"
    ),
    f"{_BASE}/aaaaaaaf/s001_2002/02_tcp_le/aaaaaaaf_s001_t000.edf": b"EDF",
    f"{_BASE}/aaaaaaax/": _index("s001_2002/"),
    f"{_BASE}/aaaaaaax/s001_2002/": _index(),
}


def test_fetch_tueg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fetching the first recording of the subjects."""
    requested = []

    def _urlopen(url: str, timeout: Any = None) -> io.BytesIO:
        requested.append(url)
        return io.BytesIO(_SERVER[url])

    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
    datadir = fetch_tueg(["aaaaaaaf"], path=tmp_path)
    assert datadir == tmp_path / "v2.0.2" / "edf"
    fname = datadir / "000/aaaaaaaf/s001_2002/02_tcp_le/aaaaaaaf_s001_t000.edf"
    assert fname.read_bytes() == b"EDF"
    assert sorted(x.name for x in fname.parent.iterdir()) == [fname.name]
    # Not downloaded again
    requested.clear()
    fetch_tueg(["aaaaaaaf"], path=tmp_path)
    assert requested == []
    with pytest.raises(ValueError, match="no recordings"):
        fetch_tueg(["aaaaaaax"], path=tmp_path)
