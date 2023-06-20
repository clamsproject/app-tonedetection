"""
The purpose of this file is to define the metadata of the app with minimal imports. 
DO NOT CHANGE the name of the file
"""

from mmif import DocumentTypes, AnnotationTypes
from clams.app import ClamsApp
from clams.appmetadata import AppMetadata

def appmetadata() -> AppMetadata:
    """
    Function to set app-metadata values and return it as an ``AppMetadata`` obj.
    Read these documentations before changing the code below
    - https://sdk.clams.ai/appmetadata.html metadata specification. 
    - https://sdk.clams.ai/autodoc/clams.appmetadata.html python API
    
    :return: AppMetadata object holding all necessary information.
    """
    #Initialize Metadata =====================================================|
    metadata = AppMetadata(
        name="Tone_Detector",
        description="Detects spans of monotonic audio within an audio file",
        app_license="Apache 2.0",
        identifier="tonedetection",
        url=f"https://github.com/clamsproject/app-tonedetection",
    )

    #IO Spec =================================================================|
    metadata.add_input(DocumentTypes.AudioDocument)
    metadata.add_output(AnnotationTypes.TimeFrame)

    #Runtime Params ==========================================================|
    metadata.add_parameter(name='time_unit', 
                            description='the unit for annotation output',
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
                            description='length for each segment of samples to be compared',
                            type='integer',
                            default=512,
                            multivalued=False)
    
    metadata.add_parameter(name='stop_at',
                            description='stop point for audio processing (in ms). Defaults to the length of the file',
                            type='integer',
                            default='None',
                            multivalued=False)
    
    metadata.add_parameter(name='tolerance',
                            description='threshold value for a \"match\" within audio processing',
                            type='number',
                            default=1.0,
                            multivalued=False)
    
    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    metadata = appmetadata()
    for param in ClamsApp.universal_parameters:
        metadata.add_parameter(**param)
    sys.stdout.write(metadata.jsonify(pretty=True))

