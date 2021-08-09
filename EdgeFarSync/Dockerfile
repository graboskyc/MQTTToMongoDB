FROM ubuntu:18.04
LABEL maintainer="chris@grabosky.net"
LABEL version="1.0.2"
ENV CONTAINER_SHELL=bash
ENV CONTAINER=

ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# basic app installs
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y \
        python3.7 \
        python3-distutils \
        wget \
        python-apt

# force newer version of ansible
# this must be first before 3.7 change...
RUN ln -s /usr/bin/python3.6 /usr/bin/python3 -f

# force specific version of python 3.7
RUN ln -s /usr/bin/python3.7 /usr/bin/python3 -f

# install pip
RUN wget -O get-pip.py https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py

# install pip required packages
RUN python3 -m pip install dnspython pymongo 

# copy over script
COPY ./edgeFarBiDi.py /opt/edgeFarBiDi.py

# run it
CMD ["python3", "/opt/edgeFarBiDi.py"]