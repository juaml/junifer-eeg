"""Reference implementations from NICE, to test the ports.

Pure-Python implementations of ``nice.algorithms`` and ``nice.recipes``
(nice-tools/nice, AGPL-3.0), kept as close as possible to the original code.
Only removed NumPy aliases and private MNE functions were updated.

"""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

import math
import zlib
from itertools import permutations

import numpy as np
from scipy.signal import butter, filtfilt


def _define_symbols(kernel):
    result_dict = dict()
    total_symbols = math.factorial(kernel)
    cursymbol = 0
    for perm in permutations(range(kernel)):
        order = "".join(map(str, perm))
        if order not in result_dict:
            result_dict[order] = cursymbol
            cursymbol = cursymbol + 1
            result_dict[order[::-1]] = total_symbols - cursymbol
    result = []
    for v in range(total_symbols):
        for symbol, value in result_dict.items():
            if value == v:
                result += [symbol]
    return result


def _symb_python(data, kernel, tau):
    """Compute symbolic transform."""
    symbols = _define_symbols(kernel)
    dims = data.shape

    signal_sym_shape = list(dims)
    signal_sym_shape[1] = data.shape[1] - tau * (kernel - 1)
    signal_sym = np.zeros(signal_sym_shape, np.int32)

    count_shape = list(dims)
    count_shape[1] = len(symbols)

    for k in range(signal_sym_shape[1]):
        subsamples = range(k, k + kernel * tau, tau)
        ind = np.argsort(data[:, subsamples], 1)
        signal_sym[
            :,
            k,
        ] = np.apply_along_axis(  # fmt: skip
            lambda x: symbols.index("".join(map(str, x))), 1, ind
        )

    count = np.double(
        np.apply_along_axis(
            lambda x: np.bincount(x, minlength=len(symbols)), 1, signal_sym
        )
    )

    return signal_sym, (count / signal_sym_shape[1])


def _filter(data, sfreq, kernel, tau):
    """Low-pass and reshape the data, as in NICE.

    data : shape (n_epochs, n_channels, n_times), returns
    (n_channels, n_times, n_epochs).
    """
    n_epochs = len(data)
    filter_freq = np.double(sfreq) / kernel / tau
    b, a = butter(6, 2.0 * filter_freq / np.double(sfreq), "lowpass")
    data = np.hstack(data)
    return np.transpose(
        np.array(np.split(filtfilt(b, a, data), n_epochs, axis=1)),
        [1, 2, 0],
    )


def pe(data, sfreq, kernel, tau):
    """Compute the PE, shape (n_channels, n_epochs)."""
    fdata = _filter(data, sfreq, kernel, tau)
    _, count = _symb_python(fdata, kernel, tau)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.nan_to_num(-np.nansum(count * np.log(count), axis=1))
    return out / np.log(math.factorial(kernel))


def _get_weights_matrix(nsym):
    wts = np.ones((nsym, nsym))
    np.fill_diagonal(wts, 0)
    wts = np.fliplr(wts)
    np.fill_diagonal(wts, 0)
    wts = np.fliplr(wts)
    return wts


def _wsmi_python(data, count, wts):
    """Compute wsmi."""
    nchannels, nsamples, ntrials = data.shape
    nsymbols = count.shape[1]
    smi = np.zeros((nchannels, nchannels, ntrials), dtype=np.double)
    wsmi = np.zeros((nchannels, nchannels, ntrials), dtype=np.double)
    for trial in range(ntrials):
        for channel1 in range(nchannels):
            for channel2 in range(channel1 + 1, nchannels):
                pxy = np.zeros((nsymbols, nsymbols))
                for sample in range(nsamples):
                    pxy[
                        data[channel1, sample, trial],
                        data[channel2, sample, trial],
                    ] += 1
                pxy = pxy / nsamples
                for sc1 in range(nsymbols):
                    for sc2 in range(nsymbols):
                        if pxy[sc1, sc2] > 0:
                            aux = pxy[sc1, sc2] * np.log(
                                pxy[sc1, sc2]
                                / count[channel1, sc1, trial]
                                / count[channel2, sc2, trial]
                            )
                            smi[channel1, channel2, trial] += aux
                            wsmi[channel1, channel2, trial] += (
                                wts[sc1, sc2] * aux
                            )
    wsmi = wsmi / np.log(nsymbols)
    smi = smi / np.log(nsymbols)
    return wsmi, smi


def wsmi(data, sfreq, kernel, tau):
    """Compute the wSMI and SMI (without CSD), symmetric.

    Returns shape (n_channels, n_channels, n_epochs).
    """
    fdata = _filter(data, sfreq, kernel, tau)
    sym, count = _symb_python(fdata, kernel, tau)
    wts = _get_weights_matrix(count.shape[1])
    out_wsmi, out_smi = _wsmi_python(sym, count, wts)
    out_wsmi += np.transpose(out_wsmi, [1, 0, 2])
    out_smi += np.transpose(out_smi, [1, 0, 2])
    return out_wsmi, out_smi


def _symb_komplexity(signal, nbins):
    """Compute symbolic transform."""
    ssignal = np.sort(signal)
    items = signal.shape[0]
    first = int(items / 10)
    last = items - first if first > 1 else items - 1
    lower = ssignal[first]
    upper = ssignal[last]
    bsize = (upper - lower) / nbins

    osignal = np.zeros(signal.shape, dtype=np.uint8)
    maxbin = nbins - 1

    for i in range(items):
        tbin = int((signal[i] - lower) / bsize)
        osignal[i] = (
            0 if tbin < 0 else maxbin if tbin > maxbin else tbin
        ) + ord("A")

    return osignal.tobytes()


def komplexity(data, nbins):
    """Compute komplexity (K), shape (n_channels, n_epochs)."""
    ntrials, nchannels, nsamples = data.shape
    k = np.zeros((nchannels, ntrials), dtype=np.float64)
    for trial in range(ntrials):
        for channel in range(nchannels):
            string = _symb_komplexity(data[trial, channel, :], nbins)
            cstring = zlib.compress(string)
            k[channel, trial] = float(len(cstring)) / float(len(string))
    return k


def epochs_compute_cnv(epochs, tmin=None, tmax=None):
    """``nice.recipes.time_locked.epochs_compute_cnv`` (EEG only)."""
    import mne
    from scipy import linalg

    picks = mne.pick_types(epochs.info, meg=True, eeg=True)
    n_epochs = len(epochs.events)
    n_channels = len(picks)
    # we reduce over time samples
    slopes = np.zeros((n_epochs, n_channels))
    intercepts = np.zeros((n_epochs, n_channels))
    if tmax is None:
        tmax = epochs.times[-1]
    if tmin is None:
        tmin = epochs.times[0]

    fit_range = np.where(
        (epochs.times >= tmin) & (epochs.times <= tmax))[0]

    # design: intercept + increasing time
    design_matrix = np.c_[np.ones(len(fit_range)),
                          epochs.times[fit_range] - tmin]

    # estimate single trial regression over time samples
    scales = np.full(n_channels, 1e6)  # EEG scaling

    for ii, epoch in enumerate(epochs):
        y = epoch[picks][:, fit_range].T  # time is samples
        betas, _, _, _ = linalg.lstsq(a=design_matrix, b=y * scales)
        intercepts[ii] = betas[0]
        slopes[ii] = betas[1]

    return slopes, intercepts
