# junifer-eeg

[junifer](https://github.com/juaml/junifer) extension for EEG data. It ports
the feature extraction of [NICE](https://github.com/nice-tools/nice) to the
junifer pipeline, configured entirely with YAML.

## Components

Importing `junifer_eeg` (`with: junifer_eeg` in the YAML) registers:

* The `EEG` data type, with the `montage` of the recording (like `space` for
  MRI), an optional `format` (needed for ambiguous extensions like EGI
  `.raw`) and optional `files` (to concatenate a recording split in several
  files).
* `EEGDataReader`: reads the `EEG` data type with MNE, including zipped EGI
  MFF directories (`.mff.zip`).
* Preprocessors: `EEGPickChannels`, `EEGSetMontage`, `EEGFilter`,
  `EEGNotchFilter`, `EEGResample`, `EEGRenameEvents`, `EEGDropEvents`,
  `EEGFixedLengthEpochs`, `EEGEventEpochs`, `EEGAdaptiveRejection`,
  `EEGAutoReject`,
  `EEGAverageReference` and `EEGInterpolateBads`.
* Markers: power spectral density (band power, spectral entropy and edges),
  permutation entropy, Kolmogorov complexity, (weighted) symbolic mutual
  information, phase locking value and weighted phase lag index, contingent negative variation, event-related
  potentials and contrasts, window decoding and ratios of markers. Each
  comes in up to three kinds, which set the dimensionality of the output:
  `<Marker>Scalar`, `<Marker>Topography` and `<Marker>Timeseries`. The `aggregations` of a marker reduce its axes
  (e.g., the epochs' trimmed mean, then the scalp channels' mean), in the
  listed order.
* The `eeg_roi` data registry: channel ROIs (e.g., `scalp`) for each montage.

## Documentation

```
pip install -e ".[docs]"
make -C docs local
```

The documentation (in `docs/_build`) describes the components and how to
configure a pipeline.

## Credits

The markers, the preprocessing and the ROIs are ported from NICE (Copyright
(C) 2014-2018 Federico Raimondo, Denis A. Engemann and Jacobo D. Sitt, AGPL v3)
and nice-extensions (Copyright (C) 2017-2018 Federico Raimondo).
