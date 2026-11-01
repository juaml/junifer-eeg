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

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Montage
     - System
     - ROIs
   * - ``GSN-HydroCel-256``, ``GSN-HydroCel-257``
     - EGI HydroCel Geodesic Sensor Net, 256 channels (257 with the vertex
       reference)
     - ``scalp``, ``nonscalp``, ``Fz``, ``Cz``, ``Pz``, ``cnv``, ``mmn``,
       ``p3a``, ``p3b``, and the 10-20 positions ``Fp1``, ``Fp2``, ``F3``,
       ``F4``, ``C3``, ``C4``, ``P3``, ``P4``, ``T5``, ``T6``, ``Oz``
   * - ``GSN-HydroCel-128``, ``GSN-HydroCel-129``
     - EGI HydroCel Geodesic Sensor Net, 128 channels (129 with the vertex
       reference)
     - ``scalp``, ``nonscalp``, ``Fz``, ``Cz``, ``Pz``, ``cnv``, ``mmn``,
       ``p3a``, ``p3b``
   * - ``GSN-HydroCel-64_1.0``, ``GSN-HydroCel-65_1.0``
     - EGI HydroCel Geodesic Sensor Net, 64 channels (65 with the vertex
       reference)
     - ``scalp``, ``nonscalp``, ``Fz``, ``Cz``, ``Pz``, ``cnv``, ``mmn``,
       ``p3a``, ``p3b``
   * - ``biosemi128``
     - BioSemi ActiveTwo, 128 channels
     - ``scalp``, ``Fz``, ``Cz``, ``Pz``, ``cnv``, ``mmn``, ``p3a``, ``p3b``
   * - ``colin27_1005``, ``colin27_1020``, ``fsaverage_1005``,
       ``fsaverage_1010``, ``fsaverage_1020``, ``spherical_1010``,
       ``spherical_1020``, ``standard_1005``, ``standard_1020``,
       ``easycap-M1``, ``biosemi16``, ``biosemi32``, ``biosemi64``,
       ``brainproducts-RNP-BA-128``
     - 10-20 system, and its 10-10 and 10-05 extensions (e.g., ANT Neuro
       waveguard, Brain Products actiCAP, BioSemi up to 64 channels, Nexstim
       eXimia, g.tec, clinical recordings)
     - ``scalp``, ``nonscalp`` (mastoids and earlobes), ``Fz``, ``Cz``,
       ``Pz``, ``cnv``, ``mmn``, ``p3a``, ``p3b``

The ``Fz``, ``Cz`` and ``Pz`` ROIs are the channels around these positions.
The ``cnv``, ``mmn``, ``p3a`` and ``p3b`` ROIs are the channels where these
components are measured (in NICE, the contingent negative variation, the
mismatch negativity, and the P3a and P3b of the Local-Global paradigm). The
ROIs of the 10-20 system are the 10-05 positions in the region of the ROIs of
the ANT Neuro (32 channels), Brain Products (32), Nexstim eXimia (60) and
g.tec (12) caps of NICE.

Other montages, or other ROIs of a montage, can be registered with
:class:`.EEGROIRegistry`.
