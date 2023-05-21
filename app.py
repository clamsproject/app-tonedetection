# CLAMS Wrapper for tone-detector.py
# A tool for detecting monotonic audio

# Imports ============================|
import argparse
import aubio
import numpy as np
import os
import ffmpeg 

from clams import ClamsApp, Restifier, AppMetadata
from typing import Union, Tuple
from lapps.discriminators import Uri
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes

# App Wrapper ========================|
__version__ = '0.0.2'

class ToneDetection(ClamsApp):

    def _appmetadata(self) -> AppMetadata:
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._appmetadata
        metadata = AppMetadata(
            name="Tone Detector",
            description="Detects spans of monotonic audio",
            app_license="Apache 2.0",
            url=f"http://mmif.clams.ai/apps/tonesdetection/{__version__}",
            identifier='tonesdetection')
        
        metadata.add_parameter(name='time_unit', 
                               description='unit for annotation output',
                               type='string',
                               choices=['seconds','milliseconds'],
                               default='seconds',
                               multivalued=False)
        
        metadata.add_parameter(name='length_threshold',
                               description='minimum length threshold (in ms)',
                               type='integer',
                               default=2000,
                               multivalued=False)
        
        metadata.add_parameter(name='sample_size',
                               description='length of samples to be compared',
                               type='integer',
                               default=512,
                               multivalued=False)
        
        metadata.add_parameter(name='stop_at',
                               description='stop point for audio processing (in ms)',
                               type='integer',
                               default='None',
                               multivalued=False)
        
        metadata.add_parameter(name='tolerance',
                               description='threshold value for a \"match\" within audio processing',
                               type='number',
                               default=1.0,
                               multivalued=False)

        metadata.add_input(DocumentTypes.AudioDocument)
        metadata.add_output(AnnotationTypes.TimeFrame)
        return metadata

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._annotate
        if isinstance(mmif, Mmif):
            mmif_obj: Mmif = mmif
        else:
            mmif_obj: Mmif = Mmif(mmif)
        docs, files = self._get_docs(mmif_obj)
        conf = self.get_configuration(**parameters)
        
        newview = mmif_obj.new_view()
        self.sign_view(newview, conf)

        for file, location in files.items():
            newview.new_contain(AnnotationTypes.TimeFrame, 
                                timeUnit = conf["time_unit"],
                                document = file)
            
            tones = self._detect_tones(location, **conf)

            for tone_pair in tones:
                tf_anno = newview.new_annotation(AnnotationTypes.TimeFrame)
                tf_anno.add_property("start", tone_pair[0])
                tf_anno.add_property("end", tone_pair[1])
                tf_anno.add_property("frameType", "tones")

        return mmif_obj
    
    @staticmethod
    def _get_docs(mmif: Mmif):
        documents = [document for document in mmif.documents 
                     if document.at_type == DocumentTypes.AudioDocument
                     and len(document.location) > 0]
        files = {document.id: document.location_path() for document in documents}
        return documents, files

    @staticmethod
    def _detect_tones(filepath, **kwargs):
        """
        perform tone detection using average cross-correlation across consecutive samples
        """
        aud = aubio.source(filepath)
        out = []
        vec1 = np.array(aud()[0])
        vec2, read2 = aud()
        vec2 = np.array(vec2)
        start_sample = 0
        sample_size = int(kwargs["sample_size"])
        duration = sample_size

        if kwargs["stop_at"] != "None":
            endpoint = int(kwargs["stop_at"])
        else:
            endpoint = aud.duration
        
        while read2 >= sample_size and start_sample < endpoint:
            similarity = np.average(np.correlate(vec1, vec2, mode="valid"))
            sim_count = 0
            while similarity >= float(kwargs["tolerance"]):
                sim_count += 1
                duration += sample_size
                vec2, read2 = aud()
                vec2 = np.array(vec2)
                similarity = np.average(np.correlate(vec1, vec2, mode="valid"))
            if sim_count > 0:
                out.append((start_sample/aud.samplerate, (start_sample+duration)/aud.samplerate))
            sim_count = 0
            start_sample += duration
            vec1 = vec2
            vec2, read2 = aud()
            duration = sample_size
        if kwargs["time_unit"] == "seconds":
            return [x for x in out if x[1]-x[0] >= int(kwargs["length_threshold"]) / 1000]
        elif kwargs["time_unit"] == "milliseconds":
            return [(x[0]*1000, x[1]*1000) for x in out if (x[1]-x[0])*1000 >= int(kwargs["length_threshold"])]
        
# Main ===============================|

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", action="store", default="5000", help="set port to listen"
    )
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # more arguments as needed
    parsed_args = parser.parse_args()

    # create the app instance
    app = ToneDetection()

    http_app = Restifier(app, port=int(parsed_args.port)
    )
    if parsed_args.production:
        http_app.serve_production()
    else:
        http_app.run()
