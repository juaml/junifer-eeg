.. include:: links.inc

.. _understanding:

Understanding junifer-eeg
=========================

``junifer-eeg`` adds EEG components to the `junifer`_ pipeline. A junifer
pipeline goes through each element (e.g., each subject) of a dataset:

#. The **DataGrabber** finds the files of the element.
#. The **DataReader** reads them.
#. The **preprocessors** transform the data, in order.
#. Each **marker** computes features from the data.
#. The **storage** saves the features.

See the `junifer`_ documentation for the general concepts. This page
describes the EEG specifics.

The ``EEG`` data type
---------------------

Importing ``junifer_eeg`` (``with: junifer_eeg`` in the YAML) registers the
``EEG`` data type. Its patterns have these keys:

``pattern``
    The path of the recording, with the replacements (e.g., ``{subject}``).
``montage``
    The montage of the recording (e.g., ``GSN-HydroCel-256``), like the
    ``space`` of MRI data. The montage sets the channel positions and the
    ROIs defined on it (named channel selections, e.g., ``scalp``).
``format`` (optional)
    The format of the file, needed when the extension is ambiguous (e.g.,
    ``egi`` for EGI ``.raw`` files).
``files`` (optional)
    A glob pattern. The ``pattern`` is then a directory, and all the files in
    it matching ``files`` are read and concatenated, sorted by recording date
    (e.g., the blocks of a task recorded in several files).

Reading and preprocessing
-------------------------

:class:`.EEGDataReader` reads the ``EEG`` data type with `MNE-Python`_ as
continuous data (:class:`mne.io.Raw`). When several files are concatenated,
MNE annotates the boundaries between them, so the epochs that span two files
are dropped, and the event preprocessors can work on each block.

The preprocessors work on the continuous data (e.g., filtering, renaming the
events) until a preprocessor cuts the data in epochs
(:class:`.EEGFixedLengthEpochs` or :class:`.EEGEventEpochs`). The following
ones work on the epochs (e.g., the rejection of bad channels and epochs, the
reference and the interpolation of the bad channels). The markers are
computed on the epochs.

Markers, kinds and aggregations
-------------------------------

A marker computes its values along its **axes**:

``epochs``
    The epochs.
``channels``
    The channels.
``channels_y``
    The second channel of a pair, for the connectivity markers (e.g., wSMI).
``times``
    The samples of a time window, for the event-related markers.
``folds``
    The cross-validation folds, for the decoding markers.

Each marker computes one or more **features**, e.g., the power in each
frequency band, or the amplitude in each time window.

Each marker comes in up to three **kinds**, which set the dimensionality of
the stored output:

``<Marker>Scalar``
    One value per feature: all the axes are reduced.
``<Marker>Topography``
    One value per channel and feature: all the axes but ``channels`` are
    reduced.
``<Marker>Timeseries``
    One value per epoch and feature: all the axes but ``epochs`` are reduced.

The ``aggregations`` of a marker set how its axes are reduced. Each
aggregation has a name and a list of steps, one per axis to reduce, with the
function (e.g., ``mean``, ``std``, ``trim_mean`` or ``median``) and, for the
channels, the ``picks``: names of ROIs of the montage or of channels,
concatenated (e.g., ``scalp``, ``[fz, cz]`` or ``[fz, Oz]``). Each aggregation
is stored as a feature of the marker, named ``<marker name>_<aggregation>``.

The steps are applied **in the order of the list**. The order matters for all
the functions but the mean: e.g., the trimmed mean across epochs of the mean
across channels is not the mean across channels of the trimmed mean across
epochs. As in NICE (Sitt et al. 2014, Engemann et al. 2018), the epochs are
usually reduced first, then the channels, then the other axes:

.. code-block:: yaml

    aggregations:
      # The trimmed mean across epochs, then the mean of the scalp channels
      trim_mean80:
        - axis: epochs
          method: trim_mean
          method_params:
            proportiontocut: 0.1
        - axis: channels
          method: mean
          picks: scalp

The estimators that are costly and shared by several markers (e.g., the power
spectral density or the symbolic transformation of wSMI) are cached, so they
are computed once per element.
