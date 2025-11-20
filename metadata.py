"""
The purpose of this file is to define the metadata of the app with minimal imports. 
DO NOT CHANGE the name of the file
"""

from clams.app import ClamsApp
from clams.appmetadata import AppMetadata
from mmif import DocumentTypes, AnnotationTypes


def appmetadata() -> AppMetadata:
    """
    Function to set app-metadata values and return it as an ``AppMetadata`` obj.
    Read these documentations before changing the code below
    - https://sdk.clams.ai/appmetadata.html metadata specification. 
    - https://sdk.clams.ai/autodoc/clams.appmetadata.html python API
    
    :return: AppMetadata object holding all necessary information.
    """
    metadata = AppMetadata(
        name="Tonedetection",
        description="Detects spans of monotonic audio within an audio file",
        app_license="Apache 2.0",
        identifier="tonedetection",
        url=f"https://github.com/clamsproject/app-tonedetection",
    )

    metadata.add_input_oneof(DocumentTypes.AudioDocument,
                             DocumentTypes.VideoDocument)
    metadata.add_output(AnnotationTypes.TimeFrame, label="tone")


    metadata.add_parameter(name='minToneDuration',
                           description='minimum length threshold (in ms)',
                           type='integer',
                           default=2000,
                           multivalued=False)

    metadata.add_parameter(name='stopAt',
                           description='stop point for audio processing (in ms). Defaults to the length of the file',
                           type='integer',
                           default=1000 * 60 * 60,  # 1 hr in ms
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
