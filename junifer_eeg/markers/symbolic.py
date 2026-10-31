"""Provide the symbolic transformation of signals (as in NICE)."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
#
# Ported from NICE (https://github.com/nice-tools/nice):
# Copyright (C) 2014-2018 Federico Raimondo, Denis A. Engemann and
# Jacobo D. Sitt

import math
from functools import cache
from itertools import permutations

import numpy as np


__all__ = ["symbol_weights", "symbolize"]


@cache
def _define_symbols(kernel: int) -> tuple[str, ...]:
    """Define the symbols: the orderings of ``kernel`` samples.

    Each ordering and its reverse are assigned symbols ``s`` and
    ``n_symbols - 1 - s``, as in NICE.

    Parameters
    ----------
    kernel : int
        The number of samples of each symbol.

    Returns
    -------
    tuple of str
        The ordering of each symbol, e.g., ``"021"``.

    """
    result_dict = {}
    total_symbols = math.factorial(kernel)
    cursymbol = 0
    for perm in permutations(range(kernel)):
        order = "".join(map(str, perm))
        if order not in result_dict:
            result_dict[order] = cursymbol
            cursymbol = cursymbol + 1
            result_dict[order[::-1]] = total_symbols - cursymbol
    symbols = {v: k for k, v in result_dict.items()}
    return tuple(symbols[v] for v in range(total_symbols))


@cache
def _symbol_lookup(kernel: int) -> np.ndarray:
    """Get the symbol of each ordering, encoded in base ``kernel``."""
    lookup = np.full(kernel**kernel, -1, dtype=np.int32)
    for symbol, order in enumerate(_define_symbols(kernel)):
        code = sum(
            int(x) * kernel ** (kernel - 1 - i) for i, x in enumerate(order)
        )
        lookup[code] = symbol
    return lookup


def symbolize(data: np.ndarray, kernel: int, tau: int) -> np.ndarray:
    """Transform signals into sequences of symbols.

    The symbol of each sample is the ordering of the ``kernel`` samples
    starting at it, ``tau`` samples apart.

    Parameters
    ----------
    data : numpy.ndarray
        The signals, shape (..., n_times).
    kernel : int
        The number of samples of each symbol.
    tau : int
        The number of samples between the samples of each symbol.

    Returns
    -------
    numpy.ndarray
        The symbols, shape (..., n_times - tau * (kernel - 1)).

    """
    n_symbols = data.shape[-1] - tau * (kernel - 1)
    idx = np.arange(n_symbols)[:, None] + tau * np.arange(kernel)[None, :]
    order = np.argsort(data[..., idx], axis=-1)
    code = np.zeros(order.shape[:-1], dtype=np.int64)
    for i in range(kernel):
        code = code * kernel + order[..., i]
    return _symbol_lookup(kernel)[code]


def symbol_weights(n_symbols: int) -> np.ndarray:
    """Get the weights of the pairs of symbols for wSMI.

    The pairs of identical and opposite symbols have weight 0, the others 1.

    Parameters
    ----------
    n_symbols : int
        The number of symbols.

    Returns
    -------
    numpy.ndarray
        The weights, shape (n_symbols, n_symbols).

    """
    weights = np.ones((n_symbols, n_symbols))
    np.fill_diagonal(weights, 0)
    weights = np.fliplr(weights)
    np.fill_diagonal(weights, 0)
    return np.fliplr(weights)
