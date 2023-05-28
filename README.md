# Tone Detector

This app detects and returns timespans in the audio track of a (potentially multimedia) file, which correspond to monotonic audio (i.e., the "tones" in SMPTE bars-and-tones).

## User instruction

General user instruction for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp/). The general user template should cover the vast majority of use cases for this app, as all user configuration for this app is done via runtime parameters.

## System requirments

The `aubio` Python library which this app uses is built on top of the `ffmpeg` multimedia processing framework. A default `ffmpeg` installation should contain everything you need to run the app as a standalone service (e.g., lib-dev codecs).

## Configurable runtime parameters

Common use cases for altering the runtime parameters include:

1. Limiting the duration of processed audio, in order to prevent superfluous processing. For example, if the tones are known to be in the first 30 seconds of the video.

2. Altering the length threshold of tones, in order to capture shorter lengths of monotonic audio.