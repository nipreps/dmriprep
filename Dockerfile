FROM ubuntu:xenial-20161213

# Used command:
# neurodocker generate docker --base=debian:stretch --pkg-manager=apt
# --ants version=latest method=source --mrtrix3 version=3.0_RC3
# --freesurfer version=6.0.0 method=binaries --fsl version=6.0.1 method=binaries

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bc \
        libtool \
        tar \
        dpkg \
        curl \
        wget \
        unzip \
        gcc \
        git \
        libstdc++6

ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ND_ENTRYPOINT" \
    &&   echo 'set -e' >> "$ND_ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ND_ENTRYPOINT" \
    &&   echo 'if [ -n "$1" ]; then "$@"; else /usr/bin/env bash; fi' >> "$ND_ENTRYPOINT"; \
    fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker

ENTRYPOINT ["/neurodocker/startup.sh"]

# SETUP taken from fmriprep:latest, installs C compiler for ANTS
# Prepare environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    curl \
                    bzip2 \
                    ca-certificates \
                    xvfb \
                    cython3 \
                    build-essential \
                    autoconf \
                    libtool \
                    pkg-config \
                    git && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y --no-install-recommends \
                    nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install latest pandoc
RUN curl -o pandoc-2.2.2.1-1-amd64.deb -sSL "https://github.com/jgm/pandoc/releases/download/2.2.2.1/pandoc-2.2.2.1-1-amd64.deb" && \
    dpkg -i pandoc-2.2.2.1-1-amd64.deb && \
    rm pandoc-2.2.2.1-1-amd64.deb

# ANTS
# from https://github.com/kaczmarj/ANTs-builds/blob/master/Dockerfile

# Get CMake for ANTS
RUN mkdir /cmake_temp
WORKDIR /cmake_temp
RUN wget https://cmake.org/files/v3.12/cmake-3.12.2.tar.gz \
    && tar -xzvf cmake-3.12.2.tar.gz \
    && echo 'done tar' \
    && ls \
    && cd cmake-3.12.2/ \
    && ./bootstrap -- -DCMAKE_BUILD_TYPE:STRING=Release \
    && make -j4 \
    && make install \
    && cd .. \
    && rm -rf *

RUN cmake --version

RUN mkdir /ants
RUN apt-get update && apt-get -y install zlib1g-dev

RUN git clone https://github.com/ANTsX/ANTs.git --branch v2.3.1 /ants
WORKDIR /ants

RUN mkdir build \
    && cd build \
    && git config --global url."https://".insteadOf git:// \
    && cmake .. \
    && make -j1 \
    && mkdir -p /opt/ants \
    && mv bin/* /opt/ants && mv ../Scripts/* /opt/ants \
    && cd .. \
    && rm -rf build

ENV ANTSPATH=/opt/ants/ \
    PATH=/opt/ants:$PATH

WORKDIR /

ENV FSLDIR="/opt/fsl-6.0.1" \
    PATH="/opt/fsl-6.0.1/bin:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           dc \
           file \
           libfontconfig1 \
           libfreetype6 \
           libgl1-mesa-dev \
           libglu1-mesa-dev \
           libgomp1 \
           libice6 \
           libxcursor1 \
           libxft2 \
           libxinerama1 \
           libxrandr2 \
           libxrender1 \
           libxt6 \
           python \
           wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FSL ..." \
    && wget -q http://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py \
    && chmod 775 fslinstaller.py
RUN /fslinstaller.py -d /opt/fsl-6.0.1 -V 6.0.1 -q

# FSL 6.0.1
# Freesurfer 6.0.0
# MRtrix3
# ANTS
# Python 3

# MRtrix3
# from https://hub.docker.com/r/neurology/mrtrix/dockerfile
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    python \
    python-numpy \
    libeigen3-dev \
    clang \
    zlib1g-dev \
    libqt4-opengl-dev \
    libgl1-mesa-dev \
    git \
    ca-certificates
RUN mkdir /mrtrix
RUN git clone https://github.com/MRtrix3/mrtrix3.git --branch 3.0_RC3 /mrtrix
WORKDIR /mrtrix
# Checkout version used in the lab: 20180128
RUN git checkout f098f097ccbb3e5efbb8f5552f13e0997d161cce
ENV CXX=/usr/bin/clang++
RUN ./configure
RUN ./build
RUN ./set_path
ENV PATH=/mrtrix/bin:$PATH

WORKDIR /

# Installing and setting up miniconda
RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh && \
    bash Miniconda3-4.5.11-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-4.5.11-Linux-x86_64.sh

# Set CPATH for packages relying on compiled libs (e.g. indexed_gzip)
ENV PATH="/usr/local/miniconda/bin:$PATH" \
    CPATH="/usr/local/miniconda/include/:$CPATH" \
    LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONNOUSERSITE=1

# add credentials on build
RUN mkdir ~/.ssh && ln -s /run/secrets/host_ssh_key ~/.ssh/id_rsa
# Getting required installation tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libopenblas-base

# Precaching atlases
ENV TEMPLATEFLOW_HOME="/opt/templateflow"
RUN mkdir -p $TEMPLATEFLOW_HOME
RUN pip install --no-cache-dir "templateflow>=0.3.0,<0.4.0a0" && \
    python -c "from templateflow import api as tfapi; \
               tfapi.get('MNI152NLin6Asym', atlas=None); \
               tfapi.get('MNI152NLin2009cAsym', atlas=None); \
               tfapi.get('OASIS30ANTs');" && \
    find $TEMPLATEFLOW_HOME -type d -exec chmod go=u {} + && \
    find $TEMPLATEFLOW_HOME -type f -exec chmod go=u {} +

RUN conda install -y python=3.7.3 \
                     pip=19.1 \
                     libxml2=2.9.8 \
                     libxslt=1.1.32 \
                     graphviz=2.40.1; sync && \
    chmod -R a+rX /usr/local/miniconda; sync && \
    chmod +x /usr/local/miniconda/bin/*; sync && \
    conda build purge-all; sync && \
    conda clean -tipsy && sync


# Setting up an install of dmripreproc (manual version) inside the container
#ADD https://api.github.com/repos/TIGRLab/dmripreproc/git/refs/heads/master version.json
#RUN git clone -b master https://github.com/TIGRLab/dmripreproc.git dmripreproc

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g svgo

# Installing bids-validator
RUN npm install -g bids-validator@1.2.5

RUN pip install --upgrade pip

RUN mkdir dmriprep
COPY ./ dmriprep/
RUN cd dmriprep && python setup.py install

ENTRYPOINT ["dmriprep"]
