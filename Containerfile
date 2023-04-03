# Use the same base image version as the clams-python python library version
FROM ghcr.io/clamsproject/clams-python-ffmpeg:0.5.3
# See https://github.com/orgs/clamsproject/packages?tab=packages&q=clams-python for more base images

################################################################################
# system dependencies
################################################################################
RUN apt-get update
RUN pip3 install numpy 
RUN apt-get install -y gcc

################################################################################
# main app installation
################################################################################
COPY ./ /app
WORKDIR /app
RUN pip3 install -r requirements.txt

# default command to run the CLAMS app in a production server 
CMD ["python3", "app.py", "--production"]
################################################################################
