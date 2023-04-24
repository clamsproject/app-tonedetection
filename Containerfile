# Uses the CLAMS Python FFMPEG base image
FROM ghcr.io/clamsproject/clams-python-ffmpeg:0.5.2
# See https://github.com/orgs/clamsproject/packages?tab=packages&q=clams-python for more base images

################################################################################
# system dependencies
################################################################################
RUN apt-get update
RUN pip install numpy
RUN apt-get install -y gcc
RUN apt-get install -y \
        libavutil-dev \
        libavcodec-dev \ 
        libavformat-dev \ 
        libavresample-dev \ 
        libswscale-dev \ 
        libswresample-dev \
        ffmpeg \ 
        && rm -rf /var/lib/apt/lists/*

################################################################################
# main app installation
################################################################################
COPY ./ /app
WORKDIR /app
RUN pip3 install -r requirements.txt

# default command to run the CLAMS app in a production server 
CMD ["python3", "app.py", "--production"]
################################################################################
