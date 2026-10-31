# junifer-eeg

[junifer](https://github.com/juaml/junifer) extension for EEG data. It ports
the feature extraction of [NICE](https://github.com/nice-tools/nice) to the
junifer pipeline, configured entirely with YAML.

## Components

Importing `junifer_eeg` (`with: junifer_eeg` in the YAML) registers:

* The `EEG` data type, with the `montage` of the recording (like `space` for
  MRI) and an optional `format` (needed for ambiguous extensions like EGI
  `.raw`).
* `EEGDataReader`: reads the `EEG` data type with MNE, including zipped EGI
  MFF directories (`.mff.zip`).
* Preprocessors: `EEGPickChannels`, `EEGSetMontage`, `EEGFilter`,
  `EEGNotchFilter`, `EEGResample`, `EEGFixedLengthEpochs`,
  `EEGAdaptiveRejection`, `EEGAverageReference` and `EEGInterpolateBads`.
* Markers: power spectral density (band power, spectral entropy and edges),
  permutation entropy, Kolmogorov complexity and (weighted) symbolic mutual
  information. Each comes in three kinds, which set the dimensionality of the
  output: `<Marker>Scalar`, `<Marker>Topography` and `<Marker>Timeseries`.
  The `aggregations` of a marker reduce its channels and epochs, e.g., with
  the scalp channels' mean and the epochs' trimmed mean.
* The `eeg_roi` data registry: channel ROIs (e.g., `scalp`) for each montage.

## Example

[`examples/yamls/icm_rs.yaml`](examples/yamls/icm_rs.yaml) reproduces the
ICM resting-state pipeline of NICE (`icm/rs`):

```
junifer run examples/yamls/icm_rs.yaml
```

The DataReader of the YAML is used by `junifer run` since
`juaml/junifer` `feat/configurable-datareader`.
