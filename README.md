# Tone Detector

This app detects and returns timespans in the audio track of a (potentially multimedia) file, which correspond to monotonic audio (i.e., the "tones" in SMPTE bars-and-tones). Created for use in [CLAMS Project](https://clams.ai/).

## User instruction

General user instructions for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

## System requirments

The `aubio` Python library which this app uses is built on top of the `ffmpeg` multimedia processing framework. A default `ffmpeg` installation should contain everything you need to run the app as a standalone service (e.g., lib-dev codecs).

## Configurable runtime parameters

Although all CLAMS apps are supposed to run as *stateless* HTTP servers, some apps can configured at request time using [URL query strings](https://en.wikipedia.org/wiki/Query_string). For runtime parameter supported by this app, please visit [CLAMS App Directory](https://apps.clams.ai) and look for the app name and version.

Specifically for this app, common use cases for altering the runtime parameters include:

1. `stopAt`: Limiting the duration of processed audio, in order to prevent superfluous processing. For example, if the tones are known to be in the first 30 seconds of the video.
2. `tolerance`: Altering the length threshold of tones, in order to capture shorter lengths of monotonic audio.
