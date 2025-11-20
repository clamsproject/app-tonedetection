import argparse
import logging
from typing import Union

import numpy as np
from pydub import AudioSegment
from clams import ClamsApp, Restifier
from mmif import Mmif, AnnotationTypes, DocumentTypes


class Tonedetection(ClamsApp):

    def __init__(self):
        super().__init__()

    def _appmetadata(self):
        #see metadata.py
        pass

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:
        if isinstance(mmif, Mmif):
            mmif_obj: Mmif = mmif
        else:
            mmif_obj: Mmif = Mmif(mmif)
        docs, files = self._get_docs(mmif_obj)

        newview = mmif_obj.new_view()
        # we want to sign the view with the raw user input, not the processed one
        self.sign_view(newview, parameters)

        for file, location in files.items():
            newview.new_contain(AnnotationTypes.TimeFrame,
                                document=file)

            tones = self._detect_tones(location, **parameters)

            for tone_pair in tones:
                tf_anno = newview.new_annotation(AnnotationTypes.TimeFrame)
                tf_anno.add_property("start", tone_pair[0])
                tf_anno.add_property("end", tone_pair[1])
                tf_anno.add_property("label", "tone")

        return mmif_obj

    @staticmethod
    def _get_docs(mmif: Mmif):
        documents = (mmif.get_documents_by_type(DocumentTypes.AudioDocument)
                     + mmif.get_documents_by_type(DocumentTypes.VideoDocument))

        files = {document.id: document.location_path() for document in documents}
        return documents, files

    def _detect_tones(self, filepath, **kwargs):
        """
        perform tone detection using average cross-correlation across consecutive samples
        """
        # Fixed sample rate and chunk size for consistent 250ms chunks
        sr = 16000
        sample_size = 4000  # 250ms at 16000 Hz

        self.logger.debug(f"Loading audio file: {filepath}")
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_channels(1).set_frame_rate(sr)  # mono, resample
        # Convert to numpy array and normalize to [-1, 1] range
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        samples = samples / (2 ** (audio.sample_width * 8 - 1))
        total_samples = len(samples)
        self.logger.debug(f"Audio loaded: {total_samples} samples, {sr} Hz, "
                          f"duration: {total_samples / sr:.2f}s")

        out = []
        tolerance = float(kwargs["tolerance"])
        self.logger.debug(f"Parameters: sampleSize={sample_size} (250ms), "
                          f"tolerance={tolerance}, "
                          f"minToneDuration={kwargs['minToneDuration']}ms")

        # Position tracking
        pos = 0

        # Reference chunk for comparison
        ref_chunk = samples[pos:pos + sample_size]
        pos += sample_size

        # Current chunk to compare against reference
        curr_chunk = samples[pos:pos + sample_size]
        chunk_len = len(curr_chunk)
        pos += sample_size

        start_sample = 0
        duration = sample_size

        endpoint = min(kwargs["stopAt"], total_samples)
        self.logger.debug(f"Processing up to {endpoint} samples")

        while chunk_len >= duration and start_sample < endpoint:
            similarity = np.average(np.correlate(ref_chunk, curr_chunk, mode="valid"))
            sim_count = 0
            while similarity >= tolerance:
                sim_count += 1
                duration += sample_size
                ref_chunk = curr_chunk  # compare consecutive chunks
                curr_chunk = samples[pos:pos + sample_size]
                pos += sample_size
                if len(curr_chunk) < sample_size:
                    break
                similarity = np.average(np.correlate(ref_chunk, curr_chunk, mode="valid"))
            if sim_count > 0:
                tone_start = start_sample / sr
                tone_end = (start_sample + duration) / sr
                self.logger.debug(f"Tone detected: {tone_start:.2f}s - {tone_end:.2f}s "
                                  f"(duration: {tone_end - tone_start:.2f}s)")
                out.append((tone_start, tone_end))
            start_sample += duration
            ref_chunk = curr_chunk
            curr_chunk = samples[pos:pos + sample_size]
            chunk_len = len(curr_chunk)
            pos += sample_size
            duration = sample_size

        # Filter by length threshold and convert to milliseconds (integers)
        threshold_ms = int(kwargs["minToneDuration"])
        result = [(int(x[0] * 1000), int(x[1] * 1000))
                  for x in out if (x[1] - x[0]) * 1000 >= threshold_ms]
        self.logger.debug(f"Detected {len(out)} tones, {len(result)} after "
                          f"filtering (>= {threshold_ms}ms)")
        return result


def get_app():
    """
    This function effectively creates an instance of the app class, without any arguments passed in, meaning, any
    external information such as initial app configuration should be set without using function arguments. The easiest
    way to do this is to set global variables before calling this.
    """
    return Tonedetection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="5000", help="set port to listen")
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # add more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    app = get_app()

    http_app = Restifier(app, port=int(parsed_args.port))
    # for running the application in production mode
    if parsed_args.production:
        http_app.serve_production()
    # development mode
    else:
        app.logger.setLevel(logging.DEBUG)
        http_app.run()
