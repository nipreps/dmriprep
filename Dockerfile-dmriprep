FROM dmriprep:dev

ADD . /dmriprep
WORKDIR /dmriprep
RUN /neurodocker/startup.sh python setup.py install
WORKDIR /
