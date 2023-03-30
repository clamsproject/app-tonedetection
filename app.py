# CLAMS Wrapper for tone-detector.py
# A tool for detecting monotonic audio

# Imports ============================|
import argparse
import tempfile
import subprocess 
import os, sys
import json
import aubio
import numpy as np

sys.path.insert('base_app')
from base_app import tone_detector

from clams import ClamsApp, Restifier, AppMetadata
from typing import Union, Tuple
from lapps.discriminators import Uri
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes

# App Wrapper ========================|
__version__ = '0.0.1'

class ToneDetection(ClamsApp):
    def __init__(self, model_size="medium"):
        raise NotImplementedError

    def _appmetadata(self) -> AppMetadata:
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._appmetadata
        app_version = __version__
        tone_detec_version = '0.0.1'
        metadata = AppMetadata(
            name="Tone Detector",
            description="Wraps a monotonic audio detector. The detector being wrapped was developed in-house at Brandeis"
                        "University by Dean Cahill.",
            app_version=app_version,
            app_license="Apache 2.0"

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

    def _get_docs(mmif: Mmif) -> tuple[list, list]:
        documents = [document for document in mmif.documents 
                     if document.at_type == DocumentTypes.AudioDocument
                     and len(document.location) > 0]
        files = {document.id: document.location_path() for document in documents}
        return documents, files

    def _detect_tones(files, **kwargs):
        tones = tone_detector.ToneDetector(files)
        
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
