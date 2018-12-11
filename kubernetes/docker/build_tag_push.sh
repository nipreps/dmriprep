#!/bin/bash
docker build -t dmriprep:kube1 -f dockerfile-dmriprep-kube1 .
docker tag dmriprep:kube1 gcr.io/dmriprep/dmriprep:kube1
docker push gcr.io/dmriprep/dmriprep:kube1
