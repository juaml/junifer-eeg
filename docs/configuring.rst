.. include:: links.inc

.. _configuring:

Configuring a pipeline
======================

A pipeline is configured with a `YAML`_ file, run with ``junifer run``. All
the parameters of the pipeline (filters, epochs, rejection, markers and
aggregations) are set in the YAML: none are hardcoded.

Shared blocks (e.g., the parameters of a marker, or the aggregation steps)
can be defined once under a ``definitions`` key, which junifer ignores, with
YAML anchors (``&name``), and reused with aliases (``*name``) and merge keys
(``<<: *name``).

Resting state
-------------

A resting-state pipeline (as the ICM resting state of NICE): the recordings
are filtered and cut in pseudo-epochs of 800 ms, the bad channels and epochs
are rejected, and the markers are reduced to scalars and topographies.

.. code-block:: yaml

    with: junifer_eeg

    workdir: /tmp/junifer-eeg

    definitions:
      pe_params: &pe_params
        tmin: null
        tmax: 0.6
        kernel: 3
        tau: 8
      scalp_mean: &scalp_mean
        axis: channels
        method: mean
        picks: scalp
      scalp_std: &scalp_std
        axis: channels
        method: std
        picks: scalp
      trim_mean80: &trim_mean80
        axis: epochs
        method: trim_mean
        method_params:
          proportiontocut: 0.1
      epochs_std: &epochs_std
        axis: epochs
        method: std

    datagrabber:
      kind: PatternDataGrabber
      datadir: /path/to/subjects
      types:
        - EEG
      patterns:
        EEG:
          pattern: "{subject}/*icm-rs-egi.raw"
          montage: GSN-HydroCel-256
          format: egi
      replacements:
        - subject

    datareader:
      kind: EEGDataReader

    preprocess:
      - kind: EEGPickChannels
        picks: eeg
        exclude: [E257]
      - kind: EEGSetMontage
      - kind: EEGFilter
        l_freq: 0.5
        h_freq: 45.0
      - kind: EEGResample
        sfreq: 250.0
      # Pseudo-epochs of 800 ms, separated by 550 to 850 ms
      - kind: EEGFixedLengthEpochs
        duration: 0.8
        tmin: -0.2
        onset: 0.0
        jitter: [0.55, 0.85]
        baseline: null
        seed: 42
      - kind: EEGAdaptiveRejection
        reject:
          eeg: 100.0e-6
        min_channels: 0.7
        min_epochs: 200
      - kind: EEGAverageReference
      - kind: EEGInterpolateBads
        reset_bads: true

    markers:
      - name: PE
        kind: EEGPermutationEntropyScalar
        <<: *pe_params
        aggregations:
          trim_mean80: [*trim_mean80, *scalp_mean]
          std: [*epochs_std, *scalp_mean]
          gfp_trim_mean80: [*trim_mean80, *scalp_std]
          gfp_std: [*epochs_std, *scalp_std]
      - name: PE_topo
        kind: EEGPermutationEntropyTopography
        <<: *pe_params
        aggregations:
          trim_mean80: [*trim_mean80]
          std: [*epochs_std]

    storage:
      kind: HDF5FeatureStorage
      uri: /path/to/results/icm_rs.hdf5

Event-related paradigms
-----------------------

For a task (e.g., the auditory Local-Global paradigm), the events select the
epochs and the conditions of the event-related markers.

Recordings in several files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When each block is a file, the ``files`` key reads them all. The event
channels can differ between files, so they are dropped before concatenating
(the events are kept as annotations):

.. code-block:: yaml

    datagrabber:
      kind: PatternDataGrabber
      datadir: /path/to/subjects
      types:
        - EEG
      patterns:
        EEG:
          pattern: "{subject}"
          files: "*-icm-lg-egi.raw"
          montage: GSN-HydroCel-256
          format: egi
      replacements:
        - subject

    datareader:
      kind: EEGDataReader
      drop_channel_types: [stim]

Events
^^^^^^

:class:`.EEGRenameEvents` renames the events to the conditions. The meaning of
an event can depend on the block, so the rules are applied to each block: the
first rule with any of its ``when`` events in the block renames its events.
:class:`.EEGDropEvents` drops events depending on the previous one (e.g., the
frequent trials right after a rare trial). :class:`.EEGEventEpochs` cuts the
epochs around the events:

.. code-block:: yaml

    preprocess:
      - kind: EEGRenameEvents
        scope: block
        rules:
          - when: [HXX1, HXX2]
            rename: {XXX1: LSGS, XXX2: LSGS, XXY1: LDGD, XXY2: LDGD}
          - when: [HXY1, HXY2]
            rename: {XXX1: LSGD, XXX2: LSGD, XXY1: LDGS, XXY2: LDGS}
      - kind: EEGDropEvents
        events: [LSGS, LDGS]
        preceded_by: [LSGD, LDGD]
      # (filtering)
      - kind: EEGEventEpochs
        event_id: {LSGS: 30, LSGD: 40, LDGD: 50, LDGS: 60}
        tmin: -0.2
        tmax: 1.34
        baseline: [null, 0.0]

Event-related markers
^^^^^^^^^^^^^^^^^^^^^

The ERPs (:class:`.EEGEventRelatedPotentialScalar`) and the contrasts
(:class:`.EEGEventRelatedContrastScalar`) list their features (the windows or
the contrasts), each with its conditions, time window and channels
(``picks``). The ``channels`` step of their aggregations then reduces the
channels of each feature:

.. code-block:: yaml

    markers:
      - name: Contrast
        kind: EEGEventRelatedContrastScalar
        contrasts:
          # Local deviant minus local standard
          - name: mmn
            condition_a: [LDGS, LDGD]
            condition_b: [LSGS, LSGD]
            tmin: 0.74
            tmax: 0.792
            picks: [fz, cz]
        aggregations:
          trim_mean80:
            - {axis: epochs, method: trim_mean,
               method_params: {proportiontocut: 0.1}}
            - {axis: channels, method: mean}
            - {axis: times, method: mean}

The decoding (:class:`.EEGWindowDecodingScalar`) classifies the epochs of two
sets of conditions from a time window, and its only axis is the folds of the
cross-validation:

.. code-block:: yaml

    markers:
      - name: Decoding
        kind: EEGWindowDecodingScalar
        decoders:
          - name: local
            condition_a: [LDGS, LDGD]
            condition_b: [LSGS, LSGD]
            tmin: 0.6
            tmax: 0.967
        percentile: 10
        C: 1.0
        n_splits: 10
        seed: 42
        aggregations:
          mean: [{axis: folds, method: mean}]

Ratios
------

:class:`.EEGRatioScalar` divides a feature of a marker by a feature of
another (or the same) marker, for each epoch and channel, before the
aggregations (e.g., the theta over the alpha power). The markers are given
by their base class (with the ``epochs`` and ``channels`` axes) and their
parameters. The estimators shared with other markers (e.g., the PSD) are
computed once:

.. code-block:: yaml

    definitions:
      power_params: &power_params
        estimator:
          method: welch
          tmin: null
          tmax: 0.6
          fmin: 1.0
          fmax: 45.0
          method_params:
            n_fft: 4096
            n_overlap: 100
            nperseg: 128
        bands:
          theta: [4.0, 8.0]
          alpha: [8.0, 12.0]
        dB: false
        normalized: false

    markers:
      - name: Ratio
        kind: EEGRatioScalar
        ratios:
          - name: theta_alpha
            numerator:
              marker: EEGPowerSpectralDensity
              feature: theta
              params: *power_params
            denominator:
              marker: EEGPowerSpectralDensity
              feature: alpha
              params: *power_params
        aggregations:
          trim_mean80:
            - {axis: epochs, method: trim_mean,
               method_params: {proportiontocut: 0.1}}
            - {axis: channels, method: mean, picks: scalp}

Autoreject
----------

:class:`.EEGAutoReject` can replace the adaptive rejection: it repairs the
bad channels of each epoch (interpolating them) and drops the epochs with
too many, with thresholds learnt by cross-validation:

.. code-block:: yaml

    preprocess:
      # (filtering and epochs)
      - kind: EEGAutoReject
        n_interpolate: [1, 2, 4, 8]
        cv: 10
        seed: 42
        min_epochs: 0.3
      - kind: EEGAverageReference
