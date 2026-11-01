.. include:: links.inc

.. _builtin:

Built-in components
===================

Importing ``junifer_eeg`` (``with: junifer_eeg`` in the YAML) registers these
components in junifer.

DataReader
----------

.. currentmodule:: junifer_eeg.datareader

.. autosummary::
   :nosignatures:

   EEGDataReader

Preprocessors
-------------

.. currentmodule:: junifer_eeg.preprocess

On the continuous data:

.. autosummary::
   :nosignatures:

   EEGRenameChannels
   EEGPickChannels
   EEGSetMontage
   EEGFilter
   EEGNotchFilter
   EEGResample
   EEGRenameEvents
   EEGDropEvents

Cutting the epochs:

.. autosummary::
   :nosignatures:

   EEGFixedLengthEpochs
   EEGEventEpochs

On the epochs:

.. autosummary::
   :nosignatures:

   EEGAdaptiveRejection
   EEGAutoReject
   EEGAverageReference
   EEGInterpolateBads

Markers
-------

.. currentmodule:: junifer_eeg.markers

.. list-table::
   :header-rows: 1

   * - Marker
     - Axes
     - Scalar
     - Topography
     - Timeseries
   * - Power spectral density
     - epochs, channels
     - :class:`EEGPowerSpectralDensityScalar`
     - :class:`EEGPowerSpectralDensityTopography`
     - :class:`EEGPowerSpectralDensityTimeseries`
   * - Permutation entropy
     - epochs, channels
     - :class:`EEGPermutationEntropyScalar`
     - :class:`EEGPermutationEntropyTopography`
     - :class:`EEGPermutationEntropyTimeseries`
   * - Kolmogorov complexity
     - epochs, channels
     - :class:`EEGKolmogorovComplexityScalar`
     - :class:`EEGKolmogorovComplexityTopography`
     - :class:`EEGKolmogorovComplexityTimeseries`
   * - Symbolic mutual information
     - epochs, channels, channels_y
     - :class:`EEGSymbolicMutualInformationScalar`
     - :class:`EEGSymbolicMutualInformationTopography`
     - :class:`EEGSymbolicMutualInformationTimeseries`
   * - Phase locking value
     - channels, channels_y
     - :class:`EEGPhaseLockingValueScalar`
     - :class:`EEGPhaseLockingValueTopography`
     -
   * - Weighted phase lag index
     - channels, channels_y
     - :class:`EEGWeightedPhaseLagIndexScalar`
     - :class:`EEGWeightedPhaseLagIndexTopography`
     -
   * - Contingent negative variation
     - epochs, channels
     - :class:`EEGContingentNegativeVariationScalar`
     - :class:`EEGContingentNegativeVariationTopography`
     - :class:`EEGContingentNegativeVariationTimeseries`
   * - Event-related potentials
     - epochs, channels, times
     - :class:`EEGEventRelatedPotentialScalar`
     - :class:`EEGEventRelatedPotentialTopography`
     -
   * - Event-related contrasts
     - epochs, channels, times
     - :class:`EEGEventRelatedContrastScalar`
     - :class:`EEGEventRelatedContrastTopography`
     -
   * - Ratio of two markers
     - epochs, channels
     - :class:`EEGRatioScalar`
     - :class:`EEGRatioTopography`
     - :class:`EEGRatioTimeseries`
   * - Window decoding
     - folds
     - :class:`EEGWindowDecodingScalar`
     -
     -

Montages
--------

The montages with ROIs (named channel selections) defined, for the ``picks``
of the aggregation steps:

.. list-table::
   :header-rows: 1

   * - Montage
     - ROIs
   * - ``GSN-HydroCel-256``
     - ``scalp``, ``nonscalp``, ``cnv``, ``mmn``, ``p3a``, ``p3b``
   * - ``GSN-HydroCel-128``
     - ``scalp``, ``nonscalp``, ``cnv``, ``mmn``, ``p3a``, ``p3b``

Other montages, or other ROIs of a montage, can be registered with
:class:`.EEGROIRegistry`.
