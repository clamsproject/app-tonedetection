#Imports =====================================================================|
import argparse
from typing import Union
from clams import ClamsApp, Restifier
from mmif import Mmif, AnnotationTypes, DocumentTypes
import aubio 
import numpy as np 

#Primary Class ===============================================================|
class TonesDetector(ClamsApp):

    def __init__(self):
        super().__init__()

    def _appmetadata(self):
        #see metadata.py
        pass

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
    
    #Helper Methods ==========================================================|
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
        sample_size = int(kwargs["sampleSize"])
        duration = sample_size

        if kwargs["stop_at"] != "None":
            endpoint = int(kwargs["stopAt"])
        else:
            endpoint = aud.duration
        
        while read2 >= duration and start_sample < endpoint:
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
        if kwargs["timeUnit"] == "seconds":
            return [x for x in out if x[1]-x[0] >= int(kwargs["lengthThreshold"]) / 1000]
        elif kwargs["timeUnit"] == "milliseconds":
            return [(x[0]*1000, x[1]*1000) for x in out if (x[1]-x[0])*1000 >= int(kwargs["lengthThreshold"])]

#Main ========================================================================|

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", action="store", default="5000", help="set port to listen"
    )
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    app = TonesDetector()

    http_app = Restifier(app, port=int(parsed_args.port)
    )
    if parsed_args.production:
        http_app.serve_production()
    else:
        http_app.run()
