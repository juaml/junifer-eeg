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
of the aggregation steps. The montage is the name of the MNE montage with the
channel positions (the ``montage`` of the ``EEG`` data type). An ROI has all
the positions of its region, and the ``picks`` keep the ones in the data: the
ROIs of a montage are used for any cap with its positions (e.g., the 10-20
caps of 19 or 64 channels).

Each montage links to the page of its ROIs, plotted, which can be shared by
several montages (e.g., the 10-20 system):

.. include:: montages/table.inc

The ``fz``, ``cz`` and ``pz`` ROIs are the channels around these positions
(lowercase, not to be taken for the channels ``Fz``, ``Cz`` and ``Pz``). The
``picks`` concatenate ROIs and channels, so the components of NICE are
measured on the combinations of these ROIs: ``[fz, cz]`` for the mismatch
negativity (MMN), the P3a and the contingent negative variation (CNV), and
``[cz, pz]`` for the P3b (NICE used only ``fz`` for the CNV of the EGI nets).
The ``fz``, ``cz`` and ``pz`` ROIs of the 10-20 system are the 10-05 positions
in the region of the ROIs of the ANT Neuro (32 channels), Brain Products (32),
Nexstim eXimia (60) and g.tec (12) caps of NICE.

Other montages, or other ROIs of a montage, can be registered with
:class:`.EEGROIRegistry`.
