"""Provide the fetcher of the TUH EEG Corpus."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import re
import shutil
import urllib.request
from pathlib import Path

from junifer.utils import logger, raise_error


__all__ = ["fetch_tueg"]


_TUEG_URL = "https://isip.piconepress.com/projects/nedc/data/tuh_eeg/tuh_eeg"

# The relative links of an Apache directory index (not the sorting links,
# the parent directory or other sites)
_HREF = re.compile(r'href="([^"?/:][^"]*)"')


def _list_dir(url: str) -> list[str]:
    """List a directory of the TUEG server.

    Parameters
    ----------
    url : str
        The URL of the directory, ending with ``/``.

    Returns
    -------
    list of str
        The sorted names of the entries (the directories end with ``/``).

    """
    with urllib.request.urlopen(url, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
    return sorted(set(_HREF.findall(html)))


def fetch_tueg(
    subjects: list[str],
    path: str | Path | None = None,
    group: str = "000",
    version: str = "v2.0.2",
) -> Path:
    """Fetch the first recording of subjects of the TUH EEG Corpus (TUEG).

    The first recording (EDF file) of the first session of each subject is
    downloaded, keeping the layout of the corpus:
    ``<group>/<subject>/<session>_<year>/<montage>/<subject>_<session>_<token>.edf``.
    The recordings already downloaded are not downloaded again.

    The TUEG is distributed by the Neural Engineering Data Consortium (NEDC)
    of Temple University, under a data agreement: register at
    https://isip.piconepress.com/projects/nedc/html/tuh_eeg/ before using it.

    Parameters
    ----------
    subjects : list of str
        The subjects (e.g., ``["aaaaaaaf"]``).
    path : str or pathlib.Path or None, optional
        The directory to download the corpus to. If None,
        ``~/junifer_eeg_data/tueg`` (default None).
    group : str, optional
        The group of directories of the subjects (default "000").
    version : str, optional
        The version of the corpus (default "v2.0.2").

    Returns
    -------
    pathlib.Path
        The directory with the groups of the corpus (``<path>/<version>/edf``),
        e.g., the ``datadir`` of a ``PatternDataGrabber``.

    Raises
    ------
    ValueError
        If a subject has no recordings.

    """
    if path is None:
        path = Path.home() / "junifer_eeg_data" / "tueg"
    datadir = Path(path) / version / "edf"
    for subject in subjects:
        subject_dir = datadir / group / subject
        if any(subject_dir.glob("*/*/*.edf")):
            logger.info(f"TUEG subject {subject} already downloaded")
            continue
        url = f"{_TUEG_URL}/{version}/edf/{group}/{subject}/"
        # The first session, montage and recording
        relpath = ""
        for _ in range(2):
            entries = [x for x in _list_dir(url + relpath) if x.endswith("/")]
            if len(entries) == 0:
                raise_error(f"TUEG subject {subject} has no recordings")
            relpath += entries[0]
        files = [x for x in _list_dir(url + relpath) if x.endswith(".edf")]
        if len(files) == 0:
            raise_error(f"TUEG subject {subject} has no recordings")
        relpath += files[0]
        fname = subject_dir / relpath
        fname.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading {url + relpath}")
        # Downloaded to a temporary file, renamed when complete
        tmp_fname = fname.with_suffix(".part")
        with (
            urllib.request.urlopen(url + relpath, timeout=60) as response,
            tmp_fname.open("wb") as fid,
        ):
            shutil.copyfileobj(response, fid)
        tmp_fname.rename(fname)
    return datadir
