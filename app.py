# CLAMS Wrapper for tone-detector.py
# A tool for detecting monotonic audio

# Imports ============================|
import argparse
import aubio
import numpy as np

from clams import ClamsApp, Restifier, AppMetadata
from typing import Union, Tuple
from lapps.discriminators import Uri
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes

# App Wrapper ========================|
__version__ = '0.0.1'

class ToneDetection(ClamsApp):

    def _appmetadata(self) -> AppMetadata:
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._appmetadata
        app_version = __version__
        tone_detec_version = '0.0.1'
        metadata = AppMetadata(
            name="Tone Detector",
            description="Detects spans of monotonic audio",
            app_version=app_version,
            app_license="Apache 2.0",
            url=f"http://mmif.clams.ai/apps/tonesdetection/{__version__}",
            identifier=f"http://mmif.clams.ai/apps/tonesdetection/{__version__}",
            parameters=[
            {
                "name":"timeUnit",
                "type":"string",
                "choices":["seconds", "milliseconds"],
                "default":"milliseconds",
                "description":"output unit"
            },
            {
                "name":"length",
                "type":"integer",
                "default":"2000",
                "description":"minimum ms length of sample to be included in the output",
            },
            {
                "name":"sample_size",
                "type":"integer",
                "default" :"512",
                "description" : "size of sample to be compared"
            },
            {
                "name":"stop_at",
                "type":"integer",
                "default":"None",
                "description": "stop point for audio processing"
            },
            {
                "name":"tolerance",
                "type":"float",
                "default":"1.0",
                "description":"the threshold value for a match within the processing"
            },
            ]
        )
        
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

        for i, file in enumerate(files):
            newview.new_contain(AnnotationTypes.TimeFrame, 
                                timeUnit = conf["timeUnit"],
                                document = docs[i].id)
            
            tones = self._detect_tones(file, conf)

            for tone_pair in tones:
                tf_anno = newview.new_annotation(AnnotationTypes.TimeFrame)
                tf_anno.add_property("start", tone_pair[0])
                tf_anno.add_property("end", tone_pair[1])
                tf_anno.add_property("frameType", "tones")
        return mmif_obj
    
    @staticmethod
    def _get_docs(mmif: Mmif) -> tuple[list, list]:
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
        duration = kwargs["sample_size"]

        if kwargs["stopAt"] is not None:
            endpoint = kwargs["stopAt"]
        else:
            endpoint = aud.duration
        
        while read2 >= kwargs["sample_size"] and start_sample < endpoint:
            similarity = np.average(np.correlate(vec1, vec2, mode="valid"))
            sim_count = 0
            while similarity >= kwargs["tolerance"]:
                sim_count += 1
                duration += kwargs["sample_size"]
                vec2, read2 = aud()
                vec2 = np.array(vec2)
                similarity = np.average(np.correlate(vec1, vec2, mode="valid"))
            if sim_count > 0:
                out.append((start_sample/aud.samplerate, (start_sample+duration)/aud.samplerate))
            sim_count = 0
            start_sample += duration
            vec1 = vec2
            vec2, read2 = aud()
            duration = kwargs["sample_size"]
        if kwargs["time_unit"] == "seconds":
            return [x for x in out if x[1]-x[0] >= kwargs["length"] / 1000]
        elif kwargs["time_unit"] == "milliseconds":
            return [x for x in out if x[1]-x[0] >= kwargs["length"]]
        
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
